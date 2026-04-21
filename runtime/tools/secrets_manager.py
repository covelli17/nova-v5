"""
Secrets Manager wrapper for Atlas PM-Agent.

Fetches per-company configuration from AWS Secrets Manager using fixed namespace
`nova/atlas/{company}/config`. In-memory TTL cache (15 min) with thread-safe
access. Error messages never leak secret values or internal paths.

Deuda técnica (ver governance/security/):
- B-2: Sin allowlist rígido de compañías (se controla vía validación de formato)
- B-3: Tracebacks originales no se loggean (pendiente logger estructurado global)
"""
from __future__ import annotations

import copy
import json
import re
import threading
import time
from typing import Optional

import boto3
from botocore.exceptions import ClientError

_NAMESPACE = "nova/atlas/{company}/config"
_COMPANY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
CACHE_TTL_SECONDS = 15 * 60  # 15 minutes

_cache: dict[str, tuple[dict, float]] = {}
_cache_lock = threading.Lock()
_client_lock = threading.Lock()
_client = None


def _get_client():
    global _client
    with _client_lock:
        if _client is None:
            _client = boto3.client("secretsmanager")
        return _client


def _secret_name(company: str) -> str:
    if not company or not _COMPANY_PATTERN.match(company):
        raise ValueError(
            f"Nombre de compania invalido: debe ser alfanumerico "
            f"(guiones y underscores permitidos)"
        )
    return _NAMESPACE.format(company=company.lower())


def _fetch_from_aws(secret_name: str, company: str) -> dict:
    client = _get_client()
    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        raise RuntimeError(
            f"No se pudo acceder a la configuracion de '{company}' ({code})"
        ) from None

    secret_string = response.get("SecretString", "")
    if not secret_string:
        raise RuntimeError(
            f"Configuracion de '{company}' vacia o no inicializada"
        )
    try:
        return json.loads(secret_string)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Configuracion de '{company}' con formato invalido"
        ) from None


def _filter_keys(data: dict, keys: Optional[list[str]], company: str) -> dict:
    if keys is None:
        return copy.deepcopy(data)
    missing = [k for k in keys if k not in data]
    if missing:
        raise KeyError(
            f"Keys ausentes en la configuracion de '{company}'. "
            f"Verifique que el secret tenga los campos requeridos."
        )
    return {k: copy.deepcopy(data[k]) for k in keys}


def get_secret(company: str, keys: Optional[list[str]] = None) -> dict:
    """Retrieve secret for company. Optionally filter to specific keys.

    Raises:
        ValueError: invalid company name.
        RuntimeError: AWS error or malformed secret.
        KeyError: requested keys not present in secret.
    """
    secret_name = _secret_name(company)
    now = time.time()

    with _cache_lock:
        if secret_name in _cache:
            data, expiry = _cache[secret_name]
            if now < expiry:
                return _filter_keys(data, keys, company)

    data = _fetch_from_aws(secret_name, company)

    with _cache_lock:
        _cache[secret_name] = (data, time.time() + CACHE_TTL_SECONDS)

    return _filter_keys(data, keys, company)


def invalidate_cache(company: Optional[str] = None) -> None:
    """Invalidate cache for one company, or all if company is None."""
    if company is None:
        with _cache_lock:
            _cache.clear()
        return
    secret_name = _secret_name(company)
    with _cache_lock:
        _cache.pop(secret_name, None)
