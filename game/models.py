from django.db import models


class Puzzle(models.Model):
    date = models.DateField(unique=True)
    answer = models.CharField(max_length=200)           # lowercase, for comparison
    answer_display = models.CharField(max_length=200)   # pretty display name
    category = models.CharField(max_length=50)
    hint = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='puzzles/originals/')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} — {self.answer_display}"

    def save(self, *args, **kwargs):
        self.answer = self.answer.lower().strip()
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
