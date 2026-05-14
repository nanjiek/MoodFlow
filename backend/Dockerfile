FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=moodflow_backend.settings \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "if [ \"$DJANGO_RUNSERVER\" = \"1\" ]; then python manage.py runserver 0.0.0.0:${PORT}; else gunicorn moodflow_backend.wsgi:application --bind 0.0.0.0:${PORT}; fi"]
