"""WSGI config for MoodFlow."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moodflow_backend.settings")

application = get_wsgi_application()
