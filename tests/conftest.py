"""Test-wide guards.

S1a is synthetic-fixture-only (OD-0017): no test may open a non-loopback network connection.
Dependency installation happens before pytest starts, so this blocks source-data access without
blocking `uv sync` (docs/engineering/repository-safeguards.md).
"""

import ipaddress
import socket

import pytest
from hypothesis import settings

# Property tests are derandomised and keep no example database, so every run (local or CI)
# exercises the same examples and a reviewer can reproduce the evidence exactly.
settings.register_profile("hio", derandomize=True, database=None)
settings.load_profile("hio")

_real_connect = socket.socket.connect


def _guarded_connect(self, address):
    host = address[0] if isinstance(address, tuple) else address
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    if not loopback and self.family in (socket.AF_INET, socket.AF_INET6):
        raise RuntimeError(f"network access blocked in S1a tests: {address!r}")
    return _real_connect(self, address)


@pytest.fixture(autouse=True, scope="session")
def _block_network():
    socket.socket.connect = _guarded_connect
    yield
    socket.socket.connect = _real_connect
