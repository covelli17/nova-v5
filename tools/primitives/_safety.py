"""Path confinement — garantiza que filesystem no escape del root permitido."""
import os
from pathlib import Path


def _get_allowed_root() -> Path:
    """Root permitido. Overridable via NOVA_ALLOWED_ROOT para tests."""
    root = os.environ.get(
        "NOVA_ALLOWED_ROOT",
        str(Path.home() / "Documents" / "Nova"),
    )
    return Path(root).expanduser().resolve()


def assert_path_in_allowed_root(path: str | Path) -> Path:
    """Resuelve path (siguiendo symlinks) y valida que esté dentro de ALLOWED_ROOT.

    Retorna el Path resuelto si es válido.
    Levanta PermissionError si escapa del root.

    strict=False permite validar paths que aún no existen (caso write_file).
    Resolver ambos lados neutraliza symlinks que apunten fuera del árbol.
    """
    allowed = _get_allowed_root()
    resolved = Path(path).expanduser().resolve(strict=False)
    if not resolved.is_relative_to(allowed):
        raise PermissionError(
            f"Path fuera de ALLOWED_ROOT: {resolved} no está en {allowed}"
        )
    return resolved
