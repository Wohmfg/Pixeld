# PixelGuess — Claude Code Project Memory

## What This Is
A daily puzzle game (like Wordle) where players guess the subject of a progressively
de-pixelated image in up to 6 attempts. Stats (streak, average guesses) stored in
localStorage. Built with Django. Deployed on Railway.

## Current State
All core features complete and deployed. 29 tests passing. GitHub-ready.

## Tech Stack
- **Backend:** Django 6.0.3, Python 3.14
- **Database:** SQLite (dev), Postgres-ready via `DATABASE_URL`
- **Frontend:** Vanilla JS + CSS (no React, no bundler)
- **Image processing:** Pillow 12.1.1
- **Stats storage:** browser localStorage (no user accounts needed)
- **Deployment:** Railway + Gunicorn + WhiteNoise

## Project Structure
```
pixelguess/          ← Django project root (settings, urls, wsgi, asgi)
game/                ← Main Django app
  models.py          ← Puzzle, PuzzleImage models
  views.py           ← Game view, guess API endpoint
  utils.py           ← Pillow pixelation + fuzzy match helper
  admin.py           ← Admin with inline image previews, transaction-safe save
  management/
    commands/
      create_puzzle.py ← CLI alternative to admin for adding puzzles
static/
  css/style.css      ← Custom properties, animations, responsive
  js/game.js         ← All game logic + localStorage stats
templates/
  base/base.html
  game/index.html    ← Main game page
  game/no_puzzle.html
media/puzzles/       ← Original uploaded images (excluded from git)
  processed/         ← Auto-generated pixelation levels (1–6)
staticfiles/         ← collectstatic output (excluded from git)
```

## Core Rules & Conventions
- One puzzle per day (keyed by date, e.g. `2026-03-05`)
- 6 pixel levels: level 1 = most pixelated, level 6 = clearest
- Each wrong guess reveals the next level
- Correct guess or 6 wrong guesses = game over for the day
- Close-but-misspelled guesses (similarity ≥ 0.75) trigger "Did you mean?" — do NOT consume a guess
- Stats live in localStorage key `pixelguess_stats`
- NO user login required
- Keep views simple — business logic in model methods or utils
- Always run `python manage.py test` before marking a task done
- Use Django's built-in admin to manage puzzles (no custom CMS needed)

## Models Overview
### Puzzle
- `date` (unique DateField) — the day this puzzle is active
- `answer` (CharField) — correct answer, lowercased on save
- `answer_display` (CharField) — formatted display name (e.g. "Eiffel Tower")
- `category` (CharField) — "place", "person", "object", "animal", etc.
- `hint` (CharField, optional) — shown after 3 wrong guesses
- `image` (ImageField) — original full-resolution image

### PuzzleImage (auto-generated)
- `puzzle` (FK → Puzzle)
- `level` (IntegerField 1–6) — 1=most pixelated, 6=original
- `image` (ImageField) — processed image file

## Pixelation Logic
Use Pillow: shrink image down to (width/factor) then resize back up.
Level factors: `{1: 64, 2: 32, 3: 16, 4: 8, 5: 3, 6: 1}`
Auto-generated on every `Puzzle.save()`. Idempotent via `get_or_create`.

## Fuzzy Matching
`game/utils.py` — `is_close_match(guess, answer)` uses `difflib.SequenceMatcher`.
- `FUZZY_THRESHOLD = 0.75`
- Triggered if similarity ≥ threshold but guess ≠ answer
- Returns `{did_you_mean: answer_display}` with no level advance
- Client shows blue "Did you mean: X?" suggestion, prefills input
- Player presses Enter again to confirm correct spelling

## API Endpoints
- `GET /` → today's puzzle page (level 1 image) or no_puzzle.html
- `GET /image/<date>/<level>/` → `{image_url}`
- `POST /guess/` → `{guess, date, current_level}` →
  - Correct: `{correct: true, game_over: true, answer_display}`
  - Fuzzy: `{correct: false, game_over: false, did_you_mean}`
  - Wrong: `{correct: false, game_over: false, level, image_url[, hint]}`
  - Game over (6th wrong): `{correct: false, game_over: true, answer_display}`
- Hint included when `current_level >= 3`

## Settings / Environment Variables
| Variable | Dev default | Production |
|---|---|---|
| `SECRET_KEY` | insecure fallback | required — set in Railway |
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `web-production-79bf2a.up.railway.app` |
| `DATABASE_URL` | — | set by Railway Postgres plugin |

## Deployment (Railway)
- `Procfile` — `web:` gunicorn 2 workers/threads; `release:` auto-migrate
- WhiteNoise serves static files in production (`CompressedManifestStaticFilesStorage`)
- `STATIC_ROOT = BASE_DIR / 'staticfiles'` — populated by `collectstatic`
- Media files are **not** persisted across Railway deploys (ephemeral filesystem)

## LocalStorage Stats Schema
```json
{
  "streak": 3,
  "maxStreak": 7,
  "totalPlayed": 12,
  "totalWon": 10,
  "guessDistribution": [0, 2, 3, 1, 2, 2],
  "lastPlayed": "2026-03-05",
  "lastResult": "win"
}
```

## Game State (per session, also localStorage)
```json
{
  "date": "2026-03-05",
  "guesses": ["paris", "london"],
  "currentLevel": 3,
  "status": "playing",
  "answerDisplay": null,
  "hint": null
}
```

## Do NOT
- Don't add user auth — keep it anonymous
- Don't use a JS framework — vanilla JS only
- Don't store game state server-side per user
- Don't forget to handle "already played today" on page load
- Don't pixelate with CSS blur — use real Pillow-processed images

## Testing
Run: `python manage.py test game` — 29 tests, all passing.

Test classes:
- `IndexViewTests` — index with/without puzzle
- `GetImageViewTests` — image URL endpoint
- `SubmitGuessViewTests` — correct/wrong/edge cases (14 tests)
- `FuzzyGuessTests` — typo detection, did_you_mean, threshold (6 tests)
- `CreatePuzzleCommandTests` — management command (5 tests)

Testing pattern: use `patch('game.utils.generate_pixel_levels')` in `make_puzzle()` to skip Pillow during tests.

## Potential Next Steps
- Persistent media storage (AWS S3 via `django-storages`) — needed for Railway production
- Switch dev database to PostgreSQL to match Railway
- Past puzzle browsing (`GET /puzzle/<date>/`)
- Answer autocomplete / suggestions from a fixed word list
