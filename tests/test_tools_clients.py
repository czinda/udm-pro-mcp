"""Tests for client management tools."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_block_client(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.clients import block_client
    result = await block_client("AA:BB:CC:DD:EE:FF", mock_ctx)
    assert "blocked" in result
    mock_api_client.post_cmd.assert_called_once_with(
        "stamgr", "block-sta", mac="aa:bb:cc:dd:ee:ff"
    )


@pytest.mark.asyncio
async def test_unblock_client(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.clients import unblock_client
    result = await unblock_client("aa:bb:cc:dd:ee:ff", mock_ctx)
    assert "unblocked" in result


@pytest.mark.asyncio
async def test_disconnect_client(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.clients import disconnect_client
    result = await disconnect_client("aa:bb:cc:dd:ee:ff", mock_ctx)
    assert "disconnected" in result


@pytest.mark.asyncio
async def test_authorize_guest(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.clients import authorize_guest
    result = await authorize_guest("aa:bb:cc:dd:ee:ff", minutes=120, ctx=mock_ctx)
    assert "authorized" in result
    assert "120 minutes" in result


@pytest.mark.asyncio
async def test_set_client_name(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [{"_id": "user123", "mac": "aa:bb:cc:dd:ee:ff"}]
    mock_api_client.put.return_value = {}
    from udm_pro_mcp.tools.clients import set_client_name
    result = await set_client_name("aa:bb:cc:dd:ee:ff", "My Laptop", mock_ctx)
    assert "My Laptop" in result
    mock_api_client.put.assert_called_once_with("rest/user/user123", {"name": "My Laptop"})
