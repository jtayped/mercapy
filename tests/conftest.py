from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture() -> Any:
    def load(name: str) -> dict[str, object]:
        with (FIXTURES / name).open(encoding="utf-8") as fixture_file:
            value = json.load(fixture_file)
        assert isinstance(value, dict)
        return value

    return load
