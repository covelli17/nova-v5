"""Run bash primitive — ejecuta comando con allowlist y timeout."""
import subprocess

ALLOWED_COMMANDS = {
    "ls", "cat", "pwd", "echo", "grep", "find", "head", "tail",
    "wc", "sort", "uniq", "cut", "awk", "sed",
    "git", "python", "python3", "pip", "pytest", "ruff", "mypy",
}


def run_bash(cmd: str, cwd: str | None = None, timeout: int = 30) -> dict:
    tokens = cmd.strip().split()
    if not tokens:
        raise ValueError("Comando vacio")
    first = tokens[0]
    if first not in ALLOWED_COMMANDS:
        raise PermissionError(
            f"Comando no permitido: {first}. "
            f"Allowlist: {sorted(ALLOWED_COMMANDS)}"
        )
    result = subprocess.run(
        cmd,
        shell=True,
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
