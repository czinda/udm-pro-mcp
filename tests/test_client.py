"""Tests for the UDM Pro API client."""

from __future__ import annotations

import pytest

from udm_pro_mcp.client import UDMProClient
from udm_pro_mcp.models import UDMConfig


def test_api_path():
    config = UDMConfig(password="test")
    client = UDMProClient(config)
    assert client._api("stat/health") == "/proxy/network/api/s/default/stat/health"


def test_api_path_custom_site():
    config = UDMConfig(password="test", site="mysite")
    client = UDMProClient(config)
    assert client._api("stat/sta") == "/proxy/network/api/s/mysite/stat/sta"


def test_headers_with_csrf():
    config = UDMConfig(password="test")
    client = UDMProClient(config)
    client._csrf_token = "abc123"
    headers = client._headers()
    assert headers["X-CSRF-Token"] == "abc123"


def test_headers_without_csrf():
    config = UDMConfig(password="test")
    client = UDMProClient(config)
    client._csrf_token = None
    headers = client._headers()
    assert "X-CSRF-Token" not in headers
