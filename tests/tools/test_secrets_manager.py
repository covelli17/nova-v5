"""Tests for runtime.tools.secrets_manager."""
from __future__ import annotations

import json
import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from runtime.tools import secrets_manager as sm


# Reset module state between tests
@pytest.fixture(autouse=True)
def reset_state():
    sm._cache.clear()
    sm._client = None
    yield
    sm._cache.clear()
    sm._client = None


# --- Naming / validation ---

def test_secret_name_construction():
    assert sm._secret_name("felirni") == "nova/atlas/felirni/config"
    assert sm._secret_name("FELIRNI") == "nova/atlas/felirni/config"


def test_invalid_company_name_rejected():
    invalid_names = ["", "../escape", "a b", "a;rm", "a/b", "a.b", "a$b", "a`b"]
    for name in invalid_names:
        with pytest.raises(ValueError):
            sm._secret_name(name)


def test_valid_company_names_accepted():
    for name in ["felirni", "curaplan", "m1", "robot-land", "inteligenc_ia"]:
        assert sm._secret_name(name).startswith("nova/atlas/")


# --- Happy path ---

def _mock_client(secret_dict):
    client = MagicMock()
    client.get_secret_value.return_value = {
        "SecretString": json.dumps(secret_dict)
    }
    return client


def test_get_secret_returns_full_dict():
    secret = {"slack_token": "xoxb-123", "db_url": "postgres://..."}
    with patch.object(sm, "_get_client", return_value=_mock_client(secret)):
        result = sm.get_secret("felirni")
    assert result == secret


def test_get_secret_filters_keys():
    secret = {"slack_token": "xoxb-123", "db_url": "postgres://...", "other": "x"}
    with patch.object(sm, "_get_client", return_value=_mock_client(secret)):
        result = sm.get_secret("felirni", keys=["slack_token"])
    assert result == {"slack_token": "xoxb-123"}
    assert "db_url" not in result


def test_missing_key_raises_keyerror():
    secret = {"slack_token": "xoxb-123"}
    with patch.object(sm, "_get_client", return_value=_mock_client(secret)):
        with pytest.raises(KeyError):
            sm.get_secret("felirni", keys=["nonexistent"])


# --- Cache behavior ---

def test_cache_hit_avoids_second_aws_call():
    secret = {"token": "abc"}
    client = _mock_client(secret)
    with patch.object(sm, "_get_client", return_value=client):
        sm.get_secret("felirni")
        sm.get_secret("felirni")
    assert client.get_secret_value.call_count == 1


def test_cache_expiry_triggers_fresh_fetch():
    secret = {"token": "abc"}
    client = _mock_client(secret)
    with patch.object(sm, "_get_client", return_value=client):
        sm.get_secret("felirni")
        # Force expiry by rewriting cache entry
        name = sm._secret_name("felirni")
        data, _ = sm._cache[name]
        sm._cache[name] = (data, time.time() - 1)
        sm.get_secret("felirni")
    assert client.get_secret_value.call_count == 2


def test_invalidate_cache_single_company():
    secret = {"token": "abc"}
    client = _mock_client(secret)
    with patch.object(sm, "_get_client", return_value=client):
        sm.get_secret("felirni")
        sm.invalidate_cache("felirni")
        sm.get_secret("felirni")
    assert client.get_secret_value.call_count == 2


def test_invalidate_cache_all():
    secret = {"token": "abc"}
    client = _mock_client(secret)
    with patch.object(sm, "_get_client", return_value=client):
        sm.get_secret("felirni")
        sm.get_secret("curaplan")
        sm.invalidate_cache()
        sm.get_secret("felirni")
    assert client.get_secret_value.call_count == 3


# --- Error handling ---

def test_aws_client_error_raises_runtime():
    client = MagicMock()
    client.get_secret_value.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException"}}, "GetSecretValue"
    )
    with patch.object(sm, "_get_client", return_value=client):
        with pytest.raises(RuntimeError):
            sm.get_secret("felirni")


def test_empty_secret_string_raises():
    client = MagicMock()
    client.get_secret_value.return_value = {"SecretString": ""}
    with patch.object(sm, "_get_client", return_value=client):
        with pytest.raises(RuntimeError):
            sm.get_secret("felirni")


def test_invalid_json_raises():
    client = MagicMock()
    client.get_secret_value.return_value = {"SecretString": "not-json{"}
    with patch.object(sm, "_get_client", return_value=client):
        with pytest.raises(RuntimeError):
            sm.get_secret("felirni")


# --- Security: no leakage ---

def test_error_message_does_not_leak_secret_value():
    secret = {"token": "super-secret-xoxb-ABCDEF123"}
    client = _mock_client(secret)
    with patch.object(sm, "_get_client", return_value=client):
        try:
            sm.get_secret("felirni", keys=["missing_key"])
        except KeyError as e:
            assert "super-secret-xoxb-ABCDEF123" not in str(e)
            assert "token" not in str(e)


def test_keyerror_does_not_leak_values():
    secret = {"slack_token": "xoxb-real-token", "db_password": "pg-real-pw"}
    client = _mock_client(secret)
    with patch.object(sm, "_get_client", return_value=client):
        try:
            sm.get_secret("felirni", keys=["missing"])
        except KeyError as e:
            msg = str(e)
            for value in secret.values():
                assert value not in msg


def test_keyerror_does_not_leak_key_names():
    """M-1 fix: KeyError must not expose which keys exist in the secret."""
    secret = {"slack_bot_token": "v1", "db_password": "v2", "stripe_key": "v3"}
    client = _mock_client(secret)
    with patch.object(sm, "_get_client", return_value=client):
        try:
            sm.get_secret("felirni", keys=["missing"])
        except KeyError as e:
            msg = str(e)
            for key in secret.keys():
                assert key not in msg, f"Key '{key}' leaked in error message"


def test_runtime_error_does_not_leak_secret_path():
    """M-2 fix: AWS errors must not expose internal secret path."""
    client = MagicMock()
    client.get_secret_value.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException"}}, "GetSecretValue"
    )
    with patch.object(sm, "_get_client", return_value=client):
        try:
            sm.get_secret("felirni")
        except RuntimeError as e:
            assert "nova/atlas" not in str(e)
            assert "/config" not in str(e)


# --- Concurrency ---

def test_cache_is_thread_safe():
    """M-3 fix: concurrent reads/writes do not corrupt cache."""
    secret = {"token": "abc"}
    call_count = {"n": 0}

    def slow_get(**kwargs):
        call_count["n"] += 1
        time.sleep(0.01)
        return {"SecretString": json.dumps(secret)}

    client = MagicMock()
    client.get_secret_value.side_effect = slow_get

    errors = []

    def worker():
        try:
            for _ in range(10):
                sm.get_secret("felirni")
        except Exception as e:
            errors.append(e)

    with patch.object(sm, "_get_client", return_value=client):
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert not errors, f"Errors in threads: {errors}"


# --- get_felirni_config() helper (added día 10) ---

def test_get_felirni_config_shortcut():
    """Helper get_felirni_config() calls get_secret with 'felirni' company name."""
    secret = {"api_url": "https://example.com", "api_key": "key123"}
    with patch.object(sm, "_get_client", return_value=_mock_client(secret)):
        result = sm.get_felirni_config()
    assert result == secret
    assert "api_url" in result
    assert "api_key" in result
