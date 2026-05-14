import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics"
    verbose_name = "Analytics"
