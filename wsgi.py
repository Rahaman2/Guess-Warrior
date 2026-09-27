"""Production entry point: gunicorn wsgi:app (one worker; game state is in memory)."""

from app import create_app

app, socketio = create_app()
