import datetime
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from game.models import Puzzle


class Command(BaseCommand):
    help = 'Create a new daily puzzle and generate its 6 pixelation levels.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date', required=True,
            help='Puzzle date in YYYY-MM-DD format',
        )
        parser.add_argument(
            '--answer', required=True,
            help='Correct answer (lowercased automatically for comparison)',
        )
        parser.add_argument(
            '--answer-display', required=True, dest='answer_display',
            help='Pretty display name shown to players (e.g. "Eiffel Tower")',
        )
        parser.add_argument(
            '--category', required=True,
            help='Category label (e.g. place, person, object, animal)',
        )
        parser.add_argument(
            '--hint', default='',
            help='Optional hint shown after 3 wrong guesses',
        )
        parser.add_argument(
            '--image', required=True,
            help='Absolute or relative path to the source image file',
        )

    def handle(self, *args, **options):
        # Validate date
        try:
            puzzle_date = datetime.date.fromisoformat(options['date'])
        except ValueError:
            raise CommandError(
                f"Invalid date '{options['date']}'. Use YYYY-MM-DD format."
            )

        # Prevent duplicates
        if Puzzle.objects.filter(date=puzzle_date).exists():
            raise CommandError(
                f"A puzzle for {puzzle_date} already exists. "
                "Delete it first or choose a different date."
            )

        # Validate image path
        image_path = Path(options['image']).resolve()
        if not image_path.exists():
            raise CommandError(f"Image file not found: {image_path}")
        if not image_path.is_file():
            raise CommandError(f"Path is not a file: {image_path}")

        # Build puzzle and save (triggers generate_pixel_levels)
        self.stdout.write(f"Creating puzzle for {puzzle_date}...")
        try:
            with open(image_path, 'rb') as f:
                puzzle = Puzzle(
                    date=puzzle_date,
                    answer=options['answer'],
                    answer_display=options['answer_display'],
                    category=options['category'],
                    hint=options['hint'],
                )
                puzzle.image.save(image_path.name, File(f), save=False)
                puzzle.save()
        except Exception as e:
            raise CommandError(f"Failed to create puzzle: {e}")

        level_count = puzzle.levels.count()
        self.stdout.write(self.style.SUCCESS(
            f"OK Puzzle created: {puzzle_date} - {options['answer_display']}"
        ))
        self.stdout.write(f"  Answer  : {puzzle.answer}")
        self.stdout.write(f"  Category: {puzzle.category}")
        self.stdout.write(f"  Hint    : {puzzle.hint or '(none)'}")
        self.stdout.write(f"  Levels  : {level_count} image(s) generated")
