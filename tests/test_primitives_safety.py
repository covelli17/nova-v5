"""Tests para path confinement en primitives."""
import pytest

from tools.primitives._safety import assert_path_in_allowed_root


@pytest.fixture
def nova_root(tmp_path, monkeypatch):
    """Monta un ALLOWED_ROOT temporal y aislado para cada test."""
    root = tmp_path / "nova"
    root.mkdir()
    monkeypatch.setenv("NOVA_ALLOWED_ROOT", str(root))
    return root.resolve()


def test_valid_path_inside_root(nova_root):
    target = nova_root / "subdir" / "file.md"
    assert assert_path_in_allowed_root(target) == target.resolve()


def test_valid_path_not_yet_existing(nova_root):
    """Paths que aún no existen deben validar (necesario para write_file)."""
    target = nova_root / "new" / "nested" / "file.txt"
    assert assert_path_in_allowed_root(target) == target.resolve()


def test_parent_traversal_rejected(nova_root):
    with pytest.raises(PermissionError):
        assert_path_in_allowed_root(nova_root / ".." / "secret.txt")


def test_absolute_path_outside_root_rejected(nova_root, tmp_path):
    outside = tmp_path / "other" / "file.txt"
    with pytest.raises(PermissionError):
        assert_path_in_allowed_root(outside)


def test_symlink_escaping_root_rejected(nova_root, tmp_path):
    """Symlink dentro del root que apunte afuera debe fallar."""
    outside_target = tmp_path / "outside.txt"
    outside_target.write_text("secret")
    link = nova_root / "innocent_link"
    link.symlink_to(outside_target)
    with pytest.raises(PermissionError):
        assert_path_in_allowed_root(link)


def test_root_itself_is_valid(nova_root):
    assert assert_path_in_allowed_root(nova_root) == nova_root
