import pytest
from runtime.tools.felirni_api import FelirniAPI, FelirniAPIError, _validate_id, _validate_url

# A-1: scheme
def test_ssrf_http_blocked():
    with pytest.raises(ValueError): _validate_url("http://api.felirni.com")

def test_ssrf_file_blocked():
    with pytest.raises(ValueError): _validate_url("file:///etc/passwd")

# A-1a: ECS task metadata (169.254.170.2) — el que faltaba
def test_ssrf_ecs_task_metadata_blocked():
    with pytest.raises(ValueError): _validate_url("https://169.254.170.2/v2/credentials/abc")

# A-1: EC2 metadata
def test_ssrf_ec2_metadata_blocked():
    with pytest.raises(ValueError): _validate_url("https://169.254.169.254/latest/meta-data")

# A-1: loopback
def test_ssrf_loopback_blocked():
    with pytest.raises(ValueError): _validate_url("https://127.0.0.1/internal")

# A-1: RFC1918
def test_ssrf_rfc1918_10_blocked():
    with pytest.raises(ValueError): _validate_url("https://10.0.0.5:8080/secret")

def test_ssrf_rfc1918_172_blocked():
    with pytest.raises(ValueError): _validate_url("https://172.16.0.1/internal")

def test_ssrf_rfc1918_192_blocked():
    with pytest.raises(ValueError): _validate_url("https://192.168.1.1/router")

# A-1: hostname válido pasa (no es IP literal)
def test_ssrf_external_hostname_passes():
    url = _validate_url("https://api.felirni.test")
    assert url == "https://api.felirni.test"

def test_ssrf_https_real_domain_passes():
    url = _validate_url("https://example.com/api/")
    assert url == "https://example.com/api"  # rstrip

# M-1: path injection
def test_id_traversal_blocked():
    with pytest.raises(ValueError): _validate_id("../etc/passwd")

def test_id_query_injection_blocked():
    with pytest.raises(ValueError): _validate_id("FL-001?admin=true")

def test_id_semicolon_blocked():
    with pytest.raises(ValueError): _validate_id("FL-001;DROP")

def test_id_space_blocked():
    with pytest.raises(ValueError): _validate_id("FL 001")

def test_id_valid_formats():
    for v in ["FL-001", "EPIC-001", "SPRINT-003", "PERSON-001", "DEC-001", "TICKET#42"]:
        assert _validate_id(v) == v

# M-2: FelirniAPIError opaco sin token
def test_api_error_no_token_leak():
    err = FelirniAPIError(404, "/tickets/FL-001")
    assert err.status_code == 404
    assert err.path == "/tickets/FL-001"
    assert "Bearer" not in str(err)
    assert "Authorization" not in str(err)
    assert not hasattr(err, "request")
    assert not hasattr(err, "response")

def test_api_error_is_runtime_error():
    assert isinstance(FelirniAPIError(500, "/epics"), RuntimeError)
