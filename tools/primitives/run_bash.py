"""Run bash primitive — ejecuta comando con allowlist, sin shell."""
import subprocess

ALLOWED_COMMANDS = {
    "ls", "cat", "pwd", "echo", "grep", "find", "head", "tail",
    "wc", "sort", "uniq", "cut", "awk", "sed",
    "git", "python", "python3", "pip", "pytest", "ruff", "mypy",
}

# Metacaracteres de shell prohibidos en cualquier argumento.
# Sin shell=True estos caracteres no se interpretan, pero los rechazamos
# explícitamente para fallar temprano con mensaje claro.
FORBIDDEN_CHARS = {";", "&", "|", "`", "$", ">", "<", "\n", "\r"}


def run_bash(cmd: str, cwd: str | None = None, timeout: int = 30) -> dict:
    tokens = cmd.strip().split()
    if not tokens:
        raise ValueError("Comando vacío")

    first = tokens[0]
    if first not in ALLOWED_COMMANDS:
        raise PermissionError(
            f"Comando no permitido: {first}. "
            f"Allowlist: {sorted(ALLOWED_COMMANDS)}"
        )

    for token in tokens:
        bad = FORBIDDEN_CHARS & set(token)
        if bad:
            raise PermissionError(
                f"Caracteres de shell no permitidos en '{token}': {sorted(bad)}"
            )

    result = subprocess.run(
        tokens,
        shell=False,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


if __name__ == "__main__":
    import sys
    result = run_bash(" ".join(sys.argv[1:]))
    print(result["stdout"])
    if result["returncode"] != 0:
        print("STDERR:", result["stderr"])
