"""
secrets_manager.py — cache TTL 15min thread-safe
Día 7: agrega soporte para secret canónico nova/atlas/felirni/config
"""
import json
import threading
import time
import boto3
from botocore.exceptions import ClientError

FELIRNI_SECRET_NAME = "nova/atlas/felirni/config"
_TTL = 900  # 15 min

_cache: dict = {}
_lock = threading.Lock()

def _now() -> float:
    return time.monotonic()

def get_secret(secret_name: str) -> dict:
    with _lock:
        entry = _cache.get(secret_name)
        if entry and (_now() - entry["ts"]) < _TTL:
            return entry["value"]
    client = boto3.client("secretsmanager", region_name="us-east-1")
    try:
        resp = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise RuntimeError(f"[secrets_manager] No se pudo obtener '{secret_name}'") from e
    value = json.loads(resp["SecretString"])
    with _lock:
        _cache[secret_name] = {"value": value, "ts": _now()}
    return value

def get_felirni_config() -> dict:
    """Shortcut canónico para el secret de Felirni."""
    return get_secret(FELIRNI_SECRET_NAME)

def invalidate(secret_name: str | None = None) -> None:
    with _lock:
        if secret_name:
            _cache.pop(secret_name, None)
        else:
            _cache.clear()
