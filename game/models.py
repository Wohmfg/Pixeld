from django.db import models


class Puzzle(models.Model):
    date = models.DateField(unique=True)
    answer = models.CharField(max_length=200)           # lowercase, for comparison
    answer_display = models.CharField(max_length=200)   # pretty display name
    category = models.CharField(max_length=50)
    hint = models.CharField(max_length=300, blank=True)
    aliases = models.TextField(
        blank=True,
        help_text='Comma-separated alternative accepted answers, e.g. "queen, the queen". Lowercased automatically.',
    )
    image = models.ImageField(upload_to='puzzles/originals/')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} — {self.answer_display}"

    def get_all_answers(self):
        """Return the canonical answer plus any aliases as a list of lowercase strings."""
        answers = [self.answer]
        for a in self.aliases.split(','):
            a = a.strip().lower()
            if a and a not in answers:
                answers.append(a)
        return answers

    def save(self, *args, **kwargs):
        self.answer = self.answer.lower().strip()
        if self.aliases:
            self.aliases = ', '.join(
                a.strip().lower() for a in self.aliases.split(',') if a.strip()
            )
        super().save(*args, **kwargs)
        from .utils import generate_pixel_levels
        generate_pixel_levels(self)


class PuzzleImage(models.Model):
    puzzle = models.ForeignKey(Puzzle, related_name='levels', on_delete=models.CASCADE)
    level = models.IntegerField()   # 1–6
    image = models.ImageField(upload_to='puzzles/processed/')

    class Meta:
        unique_together = ['puzzle', 'level']
        ordering = ['level']

    def __str__(self):
        return f"{self.puzzle.date} level {self.level}"
