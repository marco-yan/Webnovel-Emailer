import pytest

from src.auth import require_access_key


def test_access_key_accepts_match(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_KEY", "correct-horse")
    require_access_key("correct-horse")


def test_access_key_rejects_wrong_value(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_KEY", "correct-horse")
    with pytest.raises(PermissionError):
        require_access_key("wrong")


def test_access_key_requires_server_configuration(monkeypatch):
    monkeypatch.delenv("APP_ACCESS_KEY", raising=False)
    with pytest.raises(RuntimeError):
        require_access_key("anything")
