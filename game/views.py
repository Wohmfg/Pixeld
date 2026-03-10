import json
from datetime import date, timedelta

from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Puzzle, PuzzleImage
from .utils import is_close_match


def _puzzle_context(puzzle, puzzle_date_str, is_archive, prev_date, next_date):
    try:
        level1_url = puzzle.levels.get(level=1).image.url
    except PuzzleImage.DoesNotExist:
        level1_url = None
    return {
        'puzzle_date': puzzle_date_str,
        'level1_url': level1_url,
        'category': puzzle.category,
        'is_archive': is_archive,
        'prev_date': prev_date or '',
        'next_date': next_date or '',
    }


def _prev_date(before_date):
    prev = Puzzle.objects.filter(date__lt=before_date).order_by('-date').first()
    return prev.date.isoformat() if prev else ''


def _next_date(after_date):
    today = date.today()
    nxt = Puzzle.objects.filter(date__gt=after_date, date__lte=today).order_by('date').first()
    return nxt.date.isoformat() if nxt else ''


def index(request):
    today = date.today()
    try:
        puzzle = Puzzle.objects.get(date=today)
    except Puzzle.DoesNotExist:
        return render(request, 'game/no_puzzle.html', status=200)

    return render(request, 'game/index.html',
                  _puzzle_context(puzzle, today.isoformat(), False, _prev_date(today), ''))


def past_puzzle(request, date_str):
    today = date.today()
    try:
        puzzle_date = date.fromisoformat(date_str)
    except ValueError:
        raise Http404
    if puzzle_date >= today:
        raise Http404
    puzzle = get_object_or_404(Puzzle, date=puzzle_date)
    return render(request, 'game/index.html',
                  _puzzle_context(puzzle, date_str, True, _prev_date(puzzle_date), _next_date(puzzle_date)))


def get_image(request, date_str, level):
    puzzle = get_object_or_404(Puzzle, date=date_str)
    puzzle_image = get_object_or_404(PuzzleImage, puzzle=puzzle, level=level)
    return JsonResponse({'image_url': puzzle_image.image.url})


@require_POST
def submit_guess(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    guess = data.get('guess', '').lower().strip()
    date_str = data.get('date', '')

    try:
        current_level = int(data.get('current_level', 1))
        if not 1 <= current_level <= 6:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid level'}, status=400)

    if not guess:
        return JsonResponse({'error': 'Guess cannot be empty'}, status=400)

    puzzle = get_object_or_404(Puzzle, date=date_str)
    all_answers = puzzle.get_all_answers()

    if guess in all_answers:
        puzzle.record_guess_result(won=True, guess_number=current_level)
        return JsonResponse({
            'correct': True,
            'game_over': True,
            'answer_display': puzzle.answer_display,
        })

    # Fuzzy match against all accepted answers — don't consume the attempt
    if any(is_close_match(guess, a) for a in all_answers):
        return JsonResponse({
            'correct': False,
            'game_over': False,
            'did_you_mean': puzzle.answer_display,
        })

    # Wrong guess
    if current_level >= 6:
        puzzle.record_guess_result(won=False)
        return JsonResponse({
            'correct': False,
            'game_over': True,
            'answer_display': puzzle.answer_display,
        })

    next_level = current_level + 1
    try:
        next_image = puzzle.levels.get(level=next_level)
        image_url = next_image.image.url
    except PuzzleImage.DoesNotExist:
        image_url = None

    response = {
        'correct': False,
        'game_over': False,
        'level': next_level,
        'image_url': image_url,
    }
    if current_level >= 3 and puzzle.hint:
        response['hint'] = puzzle.hint

    return JsonResponse(response)
