from django.db import models, transaction


def _default_distribution():
    return [0, 0, 0, 0, 0, 0]


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

    # Aggregate play stats (whole player base)
    stat_plays = models.PositiveIntegerField(default=0)
    stat_wins = models.PositiveIntegerField(default=0)
    stat_guess_distribution = models.JSONField(default=_default_distribution)

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

    @property
    def stat_avg_guesses(self):
        """Average guesses among winners, or None if no wins yet."""
        total = sum(self.stat_guess_distribution)
        if total == 0:
            return None
        weighted = sum((i + 1) * count for i, count in enumerate(self.stat_guess_distribution))
        return round(weighted / total, 2)

    def record_guess_result(self, won, guess_number=None):
        """Atomically increment play stats. Call when a game ends."""
        with transaction.atomic():
            obj = Puzzle.objects.select_for_update().get(pk=self.pk)
            obj.stat_plays += 1
            if won and guess_number is not None:
                obj.stat_wins += 1
                dist = list(obj.stat_guess_distribution)
                if len(dist) < 6:
                    dist = [0] * 6
                dist[guess_number - 1] += 1
                obj.stat_guess_distribution = dist
            # Use update() to avoid triggering save() and image re-processing
            Puzzle.objects.filter(pk=self.pk).update(
                stat_plays=obj.stat_plays,
                stat_wins=obj.stat_wins,
                stat_guess_distribution=obj.stat_guess_distribution,
            )

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
