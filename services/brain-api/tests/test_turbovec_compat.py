"""TurboVec compatibility layer tests."""

import importlib
import sys

from aion_brain.memory.turbovec_compat import TurboVecCompat
from tests.turbovec_fakes import fake_idmap_module, fake_quant_module


def test_turbovec_compat_reports_unavailable_when_package_missing(monkeypatch) -> None:
    """Missing optional package reports cleanly."""
    monkeypatch.delitem(sys.modules, "turbovec", raising=False)
    original_import = importlib.import_module

    def fake_import(name: str):
        if name == "turbovec":
            raise ModuleNotFoundError(name)
        return original_import(name)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    compat = TurboVecCompat()

    assert compat.is_available() is False
    assert compat.availability_reason() == "turbovec_package_unavailable"


def test_turbovec_compat_works_with_fake_idmap_module(monkeypatch) -> None:
    """Compat can create, add, search, and remove with IdMapIndex shape."""
    monkeypatch.setitem(sys.modules, "turbovec", fake_idmap_module())
    compat = TurboVecCompat()

    index = compat.create_index(dimensions=2, bit_width=4)
    compat.add_vectors(index, [[1.0, 0.0], [0.0, 1.0]], [1, 2])
    scores, ids = compat.search(index, [1.0, 0.0], limit=2, allowed_ids=[1])
    compat.remove_ids(index, [1])

    assert scores == [1.0]
    assert ids == [1]
    assert compat.search(index, [1.0, 0.0], limit=2)[1] == [2]


def test_turbovec_compat_works_with_fake_turboquant_module(monkeypatch) -> None:
    """Compat can use the TurboQuantIndex API shape."""
    monkeypatch.setitem(sys.modules, "turbovec", fake_quant_module())
    compat = TurboVecCompat()

    index = compat.create_index(dimensions=2, bit_width=4)
    compat.add_vectors(index, [[1.0, 0.0]], [7])
    compat.save_index(index, "/tmp/fake.tvindex")

    assert compat.search(index, [1.0, 0.0], limit=1)[1] == [7]
