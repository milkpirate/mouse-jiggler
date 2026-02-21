"""Pytest configuration and fixtures."""
import asyncio
import pathlib
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def circuit_python_mocks():
    modules = {name: MagicMock() for name in [
        "board",
        "storage",
        "usb_cdc",
        "usb_hid",
        "digitalio",
        "time",
        "os",
        "supervisor",
        "microcontroller",
    ]}

    with patch.dict(sys.modules, modules):
        yield SimpleNamespace(**modules)


@pytest.fixture
def mouse_mock():
    mouse = MagicMock()
    mouse.move = MagicMock()
    yield mouse


@pytest.fixture
def async_sleep_mock(monkeypatch):
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)
    yield sleep_mock


@pytest.fixture
def tmpfile():
    """Create a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write("")

    yield pathlib.Path(temp_file.name)

    if pathlib.Path(temp_file.name).exists():
        pathlib.Path(temp_file.name).unlink()


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()



