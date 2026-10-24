"""The test-wide network guard is active (OD-0017: no source-data network access in S1a)."""

import socket

import pytest


def test_non_loopback_connection_is_refused():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(RuntimeError, match="network access blocked"):
        s.connect(("192.0.2.1", 80))  # TEST-NET-1, never routable
    s.close()
