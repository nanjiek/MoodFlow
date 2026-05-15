from __future__ import annotations

import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured

import moodflow_backend.settings as settings_module


def reload_settings() -> None:
    importlib.reload(settings_module)


def restore_safe_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_DEBUG", "true")
    monkeypatch.delenv("MOODFLOW_FIELD_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("MOODFLOW_FIELD_ENCRYPTION_ALLOW_FALLBACK", raising=False)
    monkeypatch.delenv("PASSWORD_RESET_DEBUG_CODE", raising=False)
    monkeypatch.delenv("PASSWORD_RESET_EXPOSE_DEBUG_CODE", raising=False)
    reload_settings()


def test_production_requires_field_encryption_key(monkeypatch: pytest.MonkeyPatch) -> None:
    restore_safe_settings(monkeypatch)
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    monkeypatch.delenv("MOODFLOW_FIELD_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("MOODFLOW_FIELD_ENCRYPTION_ALLOW_FALLBACK", "false")

    with pytest.raises(ImproperlyConfigured, match="MOODFLOW_FIELD_ENCRYPTION_KEY"):
        reload_settings()

    restore_safe_settings(monkeypatch)


def test_production_forbids_field_encryption_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    restore_safe_settings(monkeypatch)
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    monkeypatch.setenv("MOODFLOW_FIELD_ENCRYPTION_KEY", "test-key")
    monkeypatch.setenv("MOODFLOW_FIELD_ENCRYPTION_ALLOW_FALLBACK", "true")

    with pytest.raises(ImproperlyConfigured, match="MOODFLOW_FIELD_ENCRYPTION_ALLOW_FALLBACK"):
        reload_settings()

    restore_safe_settings(monkeypatch)


def test_production_allows_field_encryption_with_explicit_key(monkeypatch: pytest.MonkeyPatch) -> None:
    restore_safe_settings(monkeypatch)
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    monkeypatch.setenv("MOODFLOW_FIELD_ENCRYPTION_KEY", "test-key")
    monkeypatch.setenv("MOODFLOW_FIELD_ENCRYPTION_ALLOW_FALLBACK", "false")

    reload_settings()

    assert settings_module.DEBUG is False
    assert settings_module.FIELD_ENCRYPTION_KEY == "test-key"
    assert settings_module.FIELD_ENCRYPTION_ALLOW_FALLBACK is False

    restore_safe_settings(monkeypatch)
