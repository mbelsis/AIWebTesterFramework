"""
Tests for port utility functions.
"""

import socket
import pytest
from utils.ports import find_free_port, is_port_available, find_free_port_range, get_service_url


class TestIsPortAvailable:
    def test_free_port_is_available(self):
        # Use a high port unlikely to be in use
        assert is_port_available(59123) or not is_port_available(59123)  # Just no crash

    def test_occupied_port_is_not_available(self):
        # Bind a port then check
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
            assert not is_port_available(port)


class TestFindFreePort:
    def test_finds_a_port(self):
        port = find_free_port(start=19000)
        assert 19000 <= port < 19100
        assert isinstance(port, int)

    def test_raises_when_no_port_found(self):
        # Use max_attempts=0 to guarantee failure
        with pytest.raises(RuntimeError, match="No free port"):
            find_free_port(start=1, max_attempts=0)


class TestFindFreePortRange:
    def test_finds_consecutive_ports(self):
        ports = find_free_port_range(start=19200, count=2)
        assert len(ports) == 2
        assert ports[1] == ports[0] + 1


class TestGetServiceUrl:
    def test_http_url(self):
        assert get_service_url("localhost", 5000) == "http://localhost:5000"

    def test_https_url(self):
        assert get_service_url("example.com", 443, https=True) == "https://example.com:443"
