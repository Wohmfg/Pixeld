web: gunicorn pixelguess.wsgi --workers 2 --threads 2 --log-file -
release: python manage.py migrate --noinput
