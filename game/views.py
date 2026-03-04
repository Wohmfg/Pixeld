import json
from datetime import date

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Puzzle, PuzzleImage
from .utils import is_close_match


def index(request):
    today = date.today()
    try:
        puzzle = Puzzle.objects.get(date=today)
    except Puzzle.DoesNotExist:
        return render(request, 'game/no_puzzle.html', status=200)

    try:
        level1 = puzzle.levels.get(level=1)
        level1_url = level1.image.url
    except PuzzleImage.DoesNotExist:
        level1_url = None

    return render(request, 'game/index.html', {
        'puzzle_date': today.isoformat(),
        'level1_url': level1_url,
        'category': puzzle.category,
    })


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

    if guess == puzzle.answer:
        return JsonResponse({
            'correct': True,
            'game_over': True,
            'answer_display': puzzle.answer_display,
        })

    # Fuzzy match — don't consume the attempt
    if is_close_match(guess, puzzle.answer):
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
