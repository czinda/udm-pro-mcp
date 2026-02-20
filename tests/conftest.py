"""Shared test fixtures for UDM Pro MCP tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from udm_pro_mcp.client import UDMProClient
from udm_pro_mcp.models import UDMConfig
from udm_pro_mcp.server import AppContext


@pytest.fixture
def config():
    return UDMConfig(
        host="192.168.1.1",
        port=443,
        username="admin",
        password="test-password",
        site="default",
        verify_ssl=False,
    )


@pytest.fixture
def mock_client(config):
    """A UDMProClient with a mocked aiohttp session."""
    client = UDMProClient(config)
    client._session = MagicMock()
    client._csrf_token = "test-csrf-token"
    return client


@pytest.fixture
def mock_api_client():
    """A fully mocked client for tool tests — mock get/post/put/delete."""
    client = AsyncMock(spec=UDMProClient)
    return client


@pytest.fixture
def app_context(mock_api_client):
    return AppContext(client=mock_api_client)


@pytest.fixture
def mock_ctx(app_context):
    """A mock MCP Context whose lifespan_context returns our AppContext."""
    ctx = MagicMock()
    ctx.request_context.lifespan_context = app_context
    return ctx
