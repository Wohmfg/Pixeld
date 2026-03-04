import difflib
import io
from PIL import Image
from django.core.files.base import ContentFile


PIXEL_FACTORS = {1: 64, 2: 32, 3: 16, 4: 8, 5: 3, 6: 1}

FUZZY_THRESHOLD = 0.75


def is_close_match(guess, answer):
    """Return True if guess is similar but not identical to answer."""
    if guess == answer:
        return False  # exact match handled separately
    ratio = difflib.SequenceMatcher(None, guess, answer).ratio()
    return ratio >= FUZZY_THRESHOLD


def generate_pixel_levels(puzzle):
    """Generate 6 pixelation levels for a Puzzle. Called on every save."""
    from .models import PuzzleImage

    with Image.open(puzzle.image.path) as img:
        img = img.convert('RGB')
        w, h = img.size

        for level, factor in PIXEL_FACTORS.items():
            if factor == 1:
                # Level 6 = original, no pixelation
                out = img.copy()
            else:
                small = img.resize((max(1, w // factor), max(1, h // factor)), Image.NEAREST)
                out = small.resize((w, h), Image.NEAREST)

            buf = io.BytesIO()
            out.save(buf, format='JPEG', quality=85)
            filename = f"{puzzle.date}_level{level}.jpg"

            puzzle_image, _ = PuzzleImage.objects.get_or_create(
                puzzle=puzzle, level=level
            )
            puzzle_image.image.save(filename, ContentFile(buf.getvalue()), save=True)
