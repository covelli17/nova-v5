"""Primitives: file I/O y bash con safety rails."""
from .read_file import read_file
from .write_file import write_file
from .run_bash import run_bash

__all__ = ["read_file", "write_file", "run_bash"]
