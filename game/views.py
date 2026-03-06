import json
from datetime import date, timedelta

from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Puzzle, PuzzleImage
from .utils import is_close_match


def _puzzle_context(puzzle, puzzle_date_str, is_archive, archive_dates):
    try:
        level1_url = puzzle.levels.get(level=1).image.url
    except PuzzleImage.DoesNotExist:
        level1_url = None
    return {
        'puzzle_date': puzzle_date_str,
        'level1_url': level1_url,
        'category': puzzle.category,
        'is_archive': is_archive,
        'archive_dates': archive_dates,
    }


def index(request):
    today = date.today()
    try:
        puzzle = Puzzle.objects.get(date=today)
    except Puzzle.DoesNotExist:
        return render(request, 'game/no_puzzle.html', status=200)

    archive_dates = []
    for delta in (1, 2):
        d = today - timedelta(days=delta)
        if Puzzle.objects.filter(date=d).exists():
            archive_dates.append(d.isoformat())

    return render(request, 'game/index.html',
                  _puzzle_context(puzzle, today.isoformat(), False, archive_dates))


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
                  _puzzle_context(puzzle, date_str, True, []))


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
