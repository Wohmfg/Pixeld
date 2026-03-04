# PixelGuess — Implementation Plan

## Phase 1: Django Project Setup
**Goal:** Runnable skeleton with nothing broken.

Tasks:
1. `django-admin startproject pixelguess .`
2. `python manage.py startapp game`
3. Install deps: `pip install django pillow`
4. Settings: add `game` to INSTALLED_APPS, configure MEDIA_ROOT/MEDIA_URL, STATIC setup
5. Create `requirements.txt`
6. Run `python manage.py migrate` — should work with zero errors

Acceptance: `python manage.py runserver` starts without errors.

---

## Phase 2: Models
**Goal:** Puzzle and PuzzleImage models, admin registered, migrations run.

### `game/models.py`
```python
class Puzzle(models.Model):
    date = models.DateField(unique=True)
    answer = models.CharField(max_length=200)          # lowercase, for comparison
    answer_display = models.CharField(max_length=200)  # pretty display name
    category = models.CharField(max_length=50)
    hint = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='puzzles/originals/')

    def save(self, *args, **kwargs):
        self.answer = self.answer.lower().strip()
        super().save(*args, **kwargs)
        generate_pixel_levels(self)  # call util function

class PuzzleImage(models.Model):
    puzzle = models.ForeignKey(Puzzle, related_name='levels', on_delete=models.CASCADE)
    level = models.IntegerField()   # 1-6
    image = models.ImageField(upload_to='puzzles/processed/')

    class Meta:
        unique_together = ['puzzle', 'level']
        ordering = ['level']
```

### `game/utils.py`
```python
def generate_pixel_levels(puzzle):
    """Generate 6 pixelation levels for a puzzle using Pillow."""
    factors = {1: 32, 2: 16, 3: 8, 4: 4, 5: 2, 6: 1}
    # Open original image, for each factor:
    #   small = img.resize((w//factor, h//factor), Image.NEAREST)
    #   pixelated = small.resize((w, h), Image.NEAREST)
    #   save to BytesIO, create PuzzleImage record
    # Level 6 factor=1 means original (no pixelation)
```

### `game/admin.py`
Register both models. Puzzle admin should show date, answer, category inline
with PuzzleImage list.

Acceptance: Can upload a puzzle in Django admin and see 6 PuzzleImages created.

---

## Phase 3: Views & URLs
**Goal:** Game page loads, guess endpoint works.

### `game/views.py`

#### `index(request)`
- Get today's puzzle (by date)
- If no puzzle today, show "No puzzle today" page
- Pass puzzle date and level-1 image URL to template
- Return `game/index.html`

#### `get_image(request, date, level)`
- Fetch PuzzleImage for given puzzle date + level
- Return JSON `{image_url: "..."}`

#### `submit_guess(request)`  [POST only]
- Receive `{guess: string, date: string, current_level: int}`
- Normalise guess (lowercase, strip)
- Compare to puzzle.answer
- If correct: return `{correct: true, answer_display: "...", game_over: true}`
- If wrong and level < 6: return `{correct: false, level: current_level+1, image_url: "..."}`
- If wrong and level == 6: return `{correct: false, game_over: true, answer_display: "..."}`
- Include CSRF handling

### `game/urls.py`
```python
urlpatterns = [
    path('', views.index, name='index'),
    path('image/<str:date>/<int:level>/', views.get_image, name='get_image'),
    path('guess/', views.submit_guess, name='submit_guess'),
]
```

### `pixelguess/urls.py`
Include game.urls + media serving in debug mode.

Acceptance: GET / returns 200, POST /guess/ with correct answer returns `{correct: true}`.

---

## Phase 4: Templates & Base HTML

### `templates/base/base.html`
- DOCTYPE, viewport meta, link to style.css
- Title block, content block
- No JS framework imports

### `templates/game/index.html`
Extends base. Contains:
- Puzzle image display area (shows current pixelated image)
- Guess input + submit button
- Guess history list (shows previous wrong guesses)
- Stats modal (triggered after game over)
- "Already played today" banner if applicable
- Link to `game.js`

Layout sketch:
```
[Header: PixelGuess | streak badge]
[Image box: 400x400px pixelated image]
[Guess input field + Submit button]
[Guess history: Wrong guess 1, Wrong guess 2...]
[Hint text — appears after 3 wrong guesses]
[Game over modal: answer + share button + stats]
```

Acceptance: Page renders cleanly with image visible, form submittable.

---

## Phase 5: Frontend JavaScript (`static/js/game.js`)

### On page load:
1. Read `pixelguess_stats` from localStorage
2. Read `pixelguess_state_<date>` from localStorage
3. If state exists and date matches today → restore game state (show guesses, right image level)
4. If state.status === "won" or "lost" → show game-over modal immediately, no input

### Guess submission:
1. Grab value from input, trim + lowercase
2. POST to `/guess/` with `{guess, date, current_level}`
3. On success:
   - If `correct` → update image to level 6 (full reveal), show win modal
   - If `!correct && !game_over` → add guess to history, update image to new level
   - If `!correct && game_over` → show loss modal with answer
4. Update localStorage state after each guess
5. Update localStorage stats on game over

### Stats tracking (localStorage):
```javascript
function updateStats(won, guessCount) {
  const stats = loadStats();
  const today = getTodayString(); // "YYYY-MM-DD"
  if (stats.lastPlayed === today) return; // already counted
  stats.totalPlayed++;
  if (won) {
    stats.totalWon++;
    stats.streak++;
    stats.maxStreak = Math.max(stats.maxStreak, stats.streak);
    stats.guessDistribution[guessCount - 1]++;
  } else {
    stats.streak = 0;
  }
  stats.lastPlayed = today;
  stats.lastResult = won ? 'win' : 'loss';
  saveStats(stats);
}
```

### Share button:
Generate a text result like:
```
PixelGuess 2025-03-04
🟫🟫🟫🟫✅ (4/6)
```
Copy to clipboard, show "Copied!" toast.

Acceptance: Full game playable in browser, stats persist across page reloads.

---

## Phase 6: Styling (`static/css/style.css`)

Design goals: clean, minimal, readable on mobile.
- Max-width 480px centered
- Image box: square, 100% of container width
- Input: full width, large font
- Guess history: simple list, wrong guesses in muted color
- Modals: centered overlay with backdrop
- Hint text: italic, amber color
- Responsive: works on 320px wide screens

No CSS framework. Just custom CSS.

---

## Phase 7: Management Command for Puzzle Creation

### `game/management/commands/create_puzzle.py`
Optional helper: `python manage.py create_puzzle --date 2025-03-05 --answer "eiffel tower" ...`

More useful: make the Django admin experience good enough that no CLI is needed.
Ensure admin shows a preview of the 6 generated images inline.

---

## Phase 8: Polish & Edge Cases

- [ ] Puzzle not found for today → friendly "Come back tomorrow!" page
- [ ] Invalid guess (empty, too short) → client-side validation, no server hit
- [ ] Case-insensitive comparison (already handled by lowercasing)
- [ ] Partial match hints? (optional stretch goal — not in MVP)
- [ ] Mobile keyboard doesn't submit on Enter key → add keydown listener
- [ ] CSRF token included in fetch POST
- [ ] Image generation fails on puzzle save → show error in admin, don't save

---

## Implementation Order for Claude Code Sessions

| Session | Task | Estimated |
|---------|------|-----------|
| 1 | Phase 1 + 2 (setup + models) | ~30 min |
| 2 | Phase 3 (views + URLs) | ~20 min |
| 3 | Phase 4 + 5 (templates + JS) | ~45 min |
| 4 | Phase 6 (CSS styling) | ~20 min |
| 5 | Phase 7 + 8 (polish) | ~20 min |

Commit after each session. Tag `v0.1` when Phase 5 is done.
