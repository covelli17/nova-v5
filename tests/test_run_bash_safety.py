"""Tests para run_bash — allowlist, anti-injection, no-shell."""
import pytest

from tools.primitives.run_bash import run_bash


def test_basic_allowed_command_works():
    result = run_bash("echo hola")
    assert result["returncode"] == 0
    assert "hola" in result["stdout"]


def test_empty_command_rejected():
    with pytest.raises(ValueError):
        run_bash("")


def test_disallowed_command_rejected():
    with pytest.raises(PermissionError, match="no permitido"):
        run_bash("rm -rf /tmp/nada")


def test_semicolon_injection_rejected():
    """Antes del fix esto pasaba porque tokens[0]='ls'. Ahora debe fallar."""
    with pytest.raises(PermissionError, match="no permitidos"):
        run_bash("ls ; rm -rf /tmp/nada")


def test_ampersand_injection_rejected():
    with pytest.raises(PermissionError, match="no permitidos"):
        run_bash("ls && cat /etc/passwd")


def test_pipe_injection_rejected():
    with pytest.raises(PermissionError, match="no permitidos"):
        run_bash("ls | grep secret")


def test_backtick_injection_rejected():
    with pytest.raises(PermissionError, match="no permitidos"):
        run_bash("echo `whoami`")


def test_dollar_subshell_rejected():
    with pytest.raises(PermissionError, match="no permitidos"):
        run_bash("echo $(whoami)")


def test_redirect_rejected():
    with pytest.raises(PermissionError, match="no permitidos"):
        run_bash("echo hola > /tmp/robado.txt")


def test_newline_injection_safe():
    """str.split() elimina newlines, y shell=False no las interpreta.

    'cat' y '/etc/passwd' llegan como args a 'ls', que falla sin riesgo.
    """
    result = run_bash("ls\ncat /etc/passwd")
    assert result["returncode"] != 0


def test_shell_false_no_glob_expansion():
    """Con shell=False los globs no se expanden — se pasan literales.

    Esto valida que el comando NO pasa por shell: en shell real,
    'echo *' lista archivos; con shell=False solo imprime '*'.
    """
    result = run_bash("echo *")
    assert result["stdout"].strip() == "*"


def test_returncode_nonzero_on_failure():
    """Comando válido pero con argumento que falla debe reportar returncode."""
    result = run_bash("ls /ruta/que/no/existe/jamas")
    assert result["returncode"] != 0


def test_timeout_respected():
    """Un comando que excede timeout levanta TimeoutExpired."""
    import subprocess
    with pytest.raises(subprocess.TimeoutExpired):
        run_bash("python3 -c __import__('time').sleep(10)", timeout=1)
