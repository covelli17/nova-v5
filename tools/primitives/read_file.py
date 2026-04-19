"""Read file primitive — lee archivo como texto dentro del root permitido."""
from tools.primitives._safety import assert_path_in_allowed_root


def read_file(path: str, encoding: str = "utf-8") -> str:
    p = assert_path_in_allowed_root(path)
    if not p.exists():
        raise FileNotFoundError(f"No existe: {p}")
    if p.is_dir():
        raise IsADirectoryError(f"Es directorio: {p}")
    return p.read_text(encoding=encoding)


if __name__ == "__main__":
    import sys
    print(read_file(sys.argv[1]))
