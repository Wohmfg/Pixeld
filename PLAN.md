# PixelGuess — Implementation Record

All phases complete as of 2026-03-05.

---

## Phase 1 ✅ Django Project Setup
- `django-admin startproject pixelguess .` + `startapp game`
- Installed deps: Django 6.0.3, Pillow 12.1.1
- Settings: INSTALLED_APPS, MEDIA_ROOT/URL, STATIC setup
- `requirements.txt` created

## Phase 2 ✅ Models + Admin + Image Utils
- `Puzzle` and `PuzzleImage` models with migrations
- `game/utils.py` — `generate_pixel_levels()` using Pillow
  - Factors: `{1: 64, 2: 32, 3: 16, 4: 8, 5: 3, 6: 1}`
  - Called from `Puzzle.save()`, idempotent via `get_or_create`
- Admin: `PuzzleAdmin` with inline image previews, transaction-safe save
- Admin: `PuzzleImageAdmin` for direct level management

## Phase 3 ✅ Views & URLs
- `index` — today's puzzle or no_puzzle.html
- `get_image` — returns `{image_url}` for a given date + level
- `submit_guess` — POST endpoint with full validation
- 14 tests passing

## Phase 4 ✅ Templates & Base HTML
- `templates/base/base.html` — DOCTYPE, viewport, CSS link, blocks
- `templates/game/index.html` — image, guess form, history, modal, toast
- `templates/game/no_puzzle.html` — friendly "no puzzle today" page

## Phase 5 ✅ Frontend JavaScript
- `static/js/game.js` — full game loop:
  - localStorage state restore on page load
  - `submitGuess()` → fetch POST → handle correct/wrong/game_over
  - `updateStats()` — streak, distribution, win rate
  - Share button — emoji result string copied to clipboard
  - "Already played today" detection and modal restore

## Phase 6 ✅ CSS Styling
- `static/css/style.css` — custom properties, no framework
- Max-width 480px centered, responsive down to 320px
- Streak badge in header, hint in amber, guess history with ✅/❌
- Game-over modal with stats grid and distribution bars
- Copy toast animation

## Phase 7 ✅ Management Command
- `game/management/commands/create_puzzle.py`
- `python manage.py create_puzzle --date --answer --answer-display --category [--hint] --image`
- Validates date format, file existence, duplicate dates

## Phase 8 ✅ Edge Cases & Polish
- Empty / whitespace-only guess → 400
- Invalid level (out of range, non-integer) → 400
- Puzzle not found → 404
- Image generation failure → admin error message, DB rolled back
- CSRF token in fetch POST
- Enter key submits guess

---

## Post-Phase Additions

### Fuzzy Guess Matching ✅
- `game/utils.py` — `FUZZY_THRESHOLD = 0.75`, `is_close_match()` via `difflib.SequenceMatcher`
- `game/views.py` — fuzzy branch in `submit_guess()`, returns `{did_you_mean}` without advancing level
- `static/js/game.js` — `showSuggestion()`, input prefill, suggestion cleared on next keypress
- `templates/game/index.html` — `#guess-suggestion` element
- `static/css/style.css` — `.guess-suggestion` in blue
- 6 new tests in `FuzzyGuessTests`; 29 total, all passing

### Railway Deployment ✅
- `gunicorn` and `whitenoise` added to `requirements.txt`
- `Procfile` — gunicorn web process + migrate release step
- `pixelguess/settings.py` — `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` from env vars
- WhiteNoise middleware + `CompressedManifestStaticFilesStorage` in production
- `STATIC_ROOT` configured for `collectstatic`
- Live at: `https://web-production-79bf2a.up.railway.app`

### GitHub Preparation ✅
- `.gitignore` — excludes venv, db, media, staticfiles, .env, editor files
- `.gitattributes` — LF line endings for all source files
- `LICENSE` — MIT
- `README.md` — setup instructions, puzzle admin guide, Railway deploy steps

---

## Potential Next Steps
- Persistent media storage (AWS S3 via `django-storages`) — Railway filesystem is ephemeral
- Switch to PostgreSQL in dev to match Railway
- Past puzzle browsing page
- Answer autocomplete from a word list
