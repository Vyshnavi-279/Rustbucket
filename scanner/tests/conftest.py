import pytest

from scanner import registry


@pytest.fixture(autouse=True)
def _clear_registry_cache():
    registry.clear_cache()
    yield
    registry.clear_cache()