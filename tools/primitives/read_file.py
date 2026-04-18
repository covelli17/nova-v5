"""Read file primitive — retorna contenido como string."""
from pathlib import Path


def read_file(path: str, encoding: str = "utf-8") -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"No existe: {p}")
    if p.is_dir():
        raise IsADirectoryError(f"Es directorio: {p}")
    return p.read_text(encoding=encoding)


if __name__ == "__main__":
    import sys
    print(read_file(sys.argv[1]))
