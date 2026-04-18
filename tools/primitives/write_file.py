"""Write file primitive — escribe string a path, crea parents."""
from pathlib import Path


def write_file(
    path: str,
    content: str,
    encoding: str = "utf-8",
    overwrite: bool = True,
) -> dict:
    p = Path(path).expanduser().resolve()
    if p.exists() and not overwrite:
        raise FileExistsError(f"Ya existe: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = p.write_text(content, encoding=encoding)
    return {"path": str(p), "bytes": bytes_written}


if __name__ == "__main__":
    import sys
    print(write_file(sys.argv[1], sys.argv[2]))
