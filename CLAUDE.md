# PixelGuess — Claude Code Project Memory

## What This Is
A daily puzzle game (like Wordle) where players guess the subject of a progressively
de-pixelated image in up to 6 attempts. Stats (streak, average guesses) stored in
localStorage. Built with Django.

## Tech Stack
- **Backend:** Django 4.2+, Python 3.11+
- **Database:** SQLite (dev), Postgres-ready
- **Frontend:** Vanilla JS + CSS (no React, no bundler)
- **Image processing:** Pillow
- **Stats storage:** browser localStorage (no user accounts needed)

## Project Structure
```
pixelguess/          ← Django project root (settings etc.)
game/                ← Main Django app
  models.py          ← Puzzle, PuzzleImage models
  views.py           ← Game view, guess API endpoint
  urls.py
  admin.py           ← Admin to upload daily puzzles
static/
  css/style.css
  js/game.js         ← All game logic + localStorage stats
templates/
  base/base.html
  game/index.html    ← Main game page
media/puzzles/       ← Original uploaded images
  processed/         ← Auto-generated pixelation levels (1–6)
```

## Core Rules & Conventions
- One puzzle per day (keyed by date, e.g. `2025-03-04`)
- 6 pixel levels: level 1 = most pixelated, level 6 = clearest
- Each wrong guess reveals the next level
- Correct guess or 6 wrong guesses = game over for the day
- Stats live in localStorage key `pixelguess_stats`
- NO user login required
- Keep views simple — business logic in model methods or utils
- Always run `python manage.py test` before marking a task done
- Use Django's built-in admin to manage puzzles (no custom CMS needed yet)

## Models Overview
### Puzzle
- `date` (unique DateField) — the day this puzzle is active
- `answer` (CharField) — correct answer, lowercased
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
Level factors: {1: 32, 2: 16, 3: 8, 4: 4, 5: 2, 6: 1}
Auto-generate all 6 levels on Puzzle save (post_save signal or override save()).

## API Endpoints
- `GET /` → today's puzzle page (returns level 1 image)
- `GET /image/<date>/<level>/` → returns image URL for given level
- `POST /guess/` → JSON `{guess: "string"}` → `{correct: bool, level: int, game_over: bool, answer: string|null}`
- `GET /puzzle/<date>/` → puzzle metadata (for past puzzle browsing, optional)

## LocalStorage Stats Schema
```json
{
  "streak": 3,
  "maxStreak": 7,
  "totalPlayed": 12,
  "totalWon": 10,
  "guessDistribution": [0, 2, 3, 1, 2, 2],
  "lastPlayed": "2025-03-04",
  "lastResult": "win"
}
```

## Game State (per session, also localStorage)
```json
{
  "date": "2025-03-04",
  "guesses": ["paris", "london"],
  "currentLevel": 3,
  "status": "playing"
}
```

## Do NOT
- Don't add user auth — keep it anonymous
- Don't use a JS framework — vanilla JS only
- Don't store game state server-side per user
- Don't forget to handle "already played today" on page load
- Don't pixelate with CSS blur — use real Pillow-processed images

## Testing Checklist
- [ ] Puzzle model saves + auto-generates 6 image levels
- [ ] /guess/ endpoint returns correct JSON
- [ ] Game over when 6 wrong guesses
- [ ] Correct guess marks game as won
- [ ] LocalStorage stats update correctly
- [ ] Already-played state restored on page reload
- [ ] Admin can upload a puzzle with image
