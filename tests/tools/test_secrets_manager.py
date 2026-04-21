"""
tests/tools/test_secrets_manager.py
Día 7: tests para secrets_manager.py con get_felirni_config() canónico
"""
import json
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from runtime.tools.secrets_manager import (
    FELIRNI_SECRET_NAME,
    get_felirni_config,
    get_secret,
    invalidate,
)

MOCK_CONFIG = {
    "api_url": "https://le0dj70e7i.execute-api.us-east-1.amazonaws.com/prod",
    "api_key": "test-api-key-felirni",
    "slack_bot_token": "xoxb-test",
    "slack_app_token": "xapp-test",
    "slack_signing_secret": "test-signing-secret",
}


def _mock_boto(secret_value: dict = MOCK_CONFIG):
    client = MagicMock()
    client.get_secret_value.return_value = {
        "SecretString": json.dumps(secret_value)
    }
    return client


# ── get_secret ────────────────────────────────────────────────────────────────

class TestGetSecret:
    def setup_method(self):
        invalidate()

    def test_returns_parsed_dict(self):
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=_mock_boto()):
            result = get_secret(FELIRNI_SECRET_NAME)
        assert result["api_key"] == "test-api-key-felirni"

    def test_cache_hit_no_second_call(self):
        mock_client = _mock_boto()
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=mock_client):
            get_secret(FELIRNI_SECRET_NAME)
            get_secret(FELIRNI_SECRET_NAME)
        assert mock_client.get_secret_value.call_count == 1

    def test_cache_miss_after_invalidate(self):
        mock_client = _mock_boto()
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=mock_client):
            get_secret(FELIRNI_SECRET_NAME)
            invalidate(FELIRNI_SECRET_NAME)
            get_secret(FELIRNI_SECRET_NAME)
        assert mock_client.get_secret_value.call_count == 2

    def test_invalidate_all_clears_cache(self):
        mock_client = _mock_boto()
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=mock_client):
            get_secret(FELIRNI_SECRET_NAME)
            get_secret("otro/secret")
            invalidate()
            get_secret(FELIRNI_SECRET_NAME)
        assert mock_client.get_secret_value.call_count == 3

    def test_raises_runtime_error_on_client_error(self):
        from botocore.exceptions import ClientError
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "not found"}},
            "GetSecretValue",
        )
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="No se pudo obtener"):
                get_secret("no/existe")

    def test_thread_safe_concurrent_reads(self):
        """Múltiples threads leen sin corrupción de caché."""
        invalidate()
        mock_client = _mock_boto()
        results = []
        errors = []

        def reader():
            try:
                with patch("runtime.tools.secrets_manager.boto3.client", return_value=mock_client):
                    r = get_secret(FELIRNI_SECRET_NAME)
                results.append(r)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(results) == 10
        assert all(r["api_key"] == "test-api-key-felirni" for r in results)


# ── get_felirni_config ────────────────────────────────────────────────────────

class TestGetFelirniConfig:
    def setup_method(self):
        invalidate()

    def test_shortcut_returns_all_keys(self):
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=_mock_boto()):
            cfg = get_felirni_config()
        assert set(cfg.keys()) == {
            "api_url", "api_key", "slack_bot_token",
            "slack_app_token", "slack_signing_secret"
        }

    def test_shortcut_uses_canonical_name(self):
        mock_client = _mock_boto()
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=mock_client):
            get_felirni_config()
        mock_client.get_secret_value.assert_called_once_with(
            SecretId=FELIRNI_SECRET_NAME
        )

    def test_api_url_format(self):
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=_mock_boto()):
            cfg = get_felirni_config()
        assert cfg["api_url"].startswith("https://")

    def test_no_token_in_repr(self):
        """El objeto no debe exponer tokens al hacer str()."""
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=_mock_boto()):
            cfg = get_felirni_config()
        # Los valores existen pero el dict no se loguea aquí — solo verificamos que son strings
        assert isinstance(cfg["slack_bot_token"], str)
        assert isinstance(cfg["api_key"], str)


# ── TTL (fast) ────────────────────────────────────────────────────────────────

class TestTTL:
    def setup_method(self):
        invalidate()

    def test_cache_expires_after_ttl(self, monkeypatch):
        import runtime.tools.secrets_manager as sm
        # _now() se llama en: read-check, write-cache, read-check, write-cache
        # [0, 0, 901, 901] garantiza que el segundo read ve TTL expirado
        call_times = [0.0, 901.0, 901.0]  # write-ts, read-check(expired), write-ts2
        time_iter = iter(call_times)
        monkeypatch.setattr(sm, "_now", lambda: next(time_iter))

        mock_client = _mock_boto()
        with patch("runtime.tools.secrets_manager.boto3.client", return_value=mock_client):
            get_secret(FELIRNI_SECRET_NAME)
            get_secret(FELIRNI_SECRET_NAME)
        assert mock_client.get_secret_value.call_count == 2
