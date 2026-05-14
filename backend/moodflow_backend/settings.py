"""Base Django settings for the MoodFlow backend."""

from __future__ import annotations

import os
from importlib.util import find_spec
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def module_exists(module_name: str) -> bool:
    try:
        return find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "moodflow-dev-secret-key")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["*"] if DEBUG else [])


DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework",
]

RESERVED_PROJECT_APPS = [
    "accounts",
    "emotions",
    "content",
    "moderation",
    "analytics",
    "mlops",
]

PROJECT_APPS = [app for app in RESERVED_PROJECT_APPS if module_exists(app)]
MISSING_PROJECT_APPS = [app for app in RESERVED_PROJECT_APPS if app not in PROJECT_APPS]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + ["common"] + PROJECT_APPS


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "moodflow_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "moodflow_backend.wsgi.application"


def database_config() -> dict:
    db_engine = os.getenv("DB_ENGINE", "").strip().lower()
    mysql_requested = db_engine in {"mysql", "django.db.backends.mysql"} or bool(
        os.getenv("MYSQL_HOST") or os.getenv("DB_HOST")
    )

    if mysql_requested:
        return {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME", "moodflow"),
            "USER": os.getenv("MYSQL_USER") or os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }

    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("SQLITE_NAME", str(BASE_DIR / "db.sqlite3")),
    }


DATABASES = {"default": database_config()}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "zh-hans"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Asia/Hong_Kong")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.AdminJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "accounts.permissions.IsAdminAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": int(os.getenv("DRF_PAGE_SIZE", "20")),
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
}


CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", DEBUG)
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", True)

MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://localhost:8010")
MODEL_SERVICE_TIMEOUT = float(os.getenv("MODEL_SERVICE_TIMEOUT", "3"))


def redis_location() -> str | None:
    if os.getenv("REDIS_URL"):
        return os.getenv("REDIS_URL")
    if os.getenv("REDIS_HOST"):
        host = os.getenv("REDIS_HOST", "127.0.0.1")
        port = os.getenv("REDIS_PORT", "6379")
        db = os.getenv("REDIS_DB", "0")
        password = os.getenv("REDIS_PASSWORD")
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{host}:{port}/{db}"
    return None


REDIS_LOCATION = redis_location()
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_LOCATION,
    }
    if REDIS_LOCATION
    else {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "moodflow-local-cache",
    }
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
}
