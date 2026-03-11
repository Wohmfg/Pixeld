# Pixle

A daily puzzle game where you identify a progressively de-pixelated image in up to 6 guesses — inspired by Wordle.

## How it works

- Each day a new image puzzle is available
- The image starts heavily pixelated (level 1) and becomes clearer with each wrong guess
- You have 6 attempts to identify the subject
- A hint appears after your third wrong guess
- Close-but-misspelled guesses trigger a "Did you mean?" suggestion without consuming an attempt
- Stats (streak, win rate, guess distribution) are stored locally in your browser — no account needed
- After completing a puzzle, navigate to previous and next puzzles by date

## Tech stack

- **Backend:** Django 6, Python 3.11+
- **Frontend:** Vanilla JS + CSS (no framework, no bundler)
- **Image processing:** Pillow
- **Stats:** browser `localStorage` (personal) + database (aggregate per puzzle)
- **Media storage:** Cloudflare R2 via `django-storages` (production), local filesystem (dev)
- **Deployment:** Railway + Gunicorn + WhiteNoise

## Local development

**Prerequisites:** Python 3.11+

```bash
git clone https://github.com/your-username/pixle.git
cd pixle

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

## Adding a puzzle

Use the Django admin at `/admin/`. Upload an image and set:

| Field | Example |
|---|---|
| Date | `2026-03-05` |
| Answer | `eiffel tower` (lowercase) |
| Answer display | `Eiffel Tower` |
| Category | `place` |
| Hint | `Located in Paris, France` |
| Aliases | `the eiffel tower, tour eiffel` (optional, comma-separated) |

The six pixelation levels are generated automatically on save. Aggregate play stats (plays, wins, guess distribution) are tracked automatically and visible in the admin.

Alternatively, use the management command:

```bash
python manage.py create_puzzle \
  --date 2026-03-05 \
  --answer "eiffel tower" \
  --answer-display "Eiffel Tower" \
  --category place \
  --hint "Located in Paris, France" \
  --image /path/to/image.jpg
```

## Running tests

```bash
python manage.py test game
```

## Deploying to Railway

1. Push this repo to GitHub
2. Create a new Railway project → **Deploy from GitHub repo**
3. Add a **PostgreSQL** plugin (optional but recommended for production)
4. Set the following environment variables in Railway:

| Variable | Value |
|---|---|
| `SECRET_KEY` | a long random string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-app.up.railway.app,pixle.site,www.pixle.site` |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app.up.railway.app,https://pixle.site,https://www.pixle.site` |
| `DATABASE_URL` | set automatically by the Postgres plugin |

5. Railway runs `python manage.py migrate --noinput` automatically via the `Procfile` `release` step before each deploy.

### Media storage (Cloudflare R2)

Set these env vars to store uploaded images on R2 instead of the ephemeral Railway filesystem:

| Variable | Value |
|---|---|
| `R2_ACCOUNT_ID` | your Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | R2 API token key ID |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret |
| `R2_BUCKET_NAME` | your bucket name |
| `R2_CUSTOM_DOMAIN` | e.g. `pub-<hash>.r2.dev` (optional) |

If these vars are absent the app falls back to local `media/` storage (fine for development).

## Project structure

```
pixelguess/       Django project (settings, urls, wsgi)
game/             Main app — models, views, utils, admin, tests
  models.py       Puzzle, PuzzleImage
  views.py        index, past_puzzle, get_image, submit_guess
  utils.py        Pillow pixelation + fuzzy match helper
  admin.py        Admin with inline image previews + aggregate stats
static/
  css/style.css
  js/game.js      All game logic + localStorage stats
templates/
  base/base.html
  game/index.html
  game/no_puzzle.html
```

## License

MIT — see [LICENSE](LICENSE).
