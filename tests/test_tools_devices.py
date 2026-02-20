"""Tests for device management tools."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_list_devices(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {
            "mac": "aa:bb:cc:00:11:22",
            "name": "Living Room AP",
            "model": "U6-LR",
            "type": "uap",
            "ip": "192.168.1.10",
            "version": "6.5.28",
            "adopted": True,
            "state": 1,
            "uptime": 86400,
            "num_sta": 5,
            "tx_bytes": 1000000,
            "rx_bytes": 2000000,
        }
    ]
    from udm_pro_mcp.tools.devices import list_devices
    result = await list_devices(mock_ctx)
    assert "Living Room AP" in result
    assert "U6-LR" in result
    assert "connected" in result


@pytest.mark.asyncio
async def test_list_devices_empty(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = []
    from udm_pro_mcp.tools.devices import list_devices
    result = await list_devices(mock_ctx)
    assert result == "No devices found."


@pytest.mark.asyncio
async def test_restart_device(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.devices import restart_device
    result = await restart_device("AA:BB:CC:DD:EE:FF", mock_ctx)
    assert "Restart command sent" in result
    mock_api_client.post_cmd.assert_called_once_with(
        "devmgr", "restart", mac="aa:bb:cc:dd:ee:ff"
    )


@pytest.mark.asyncio
async def test_locate_device_on(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.devices import locate_device
    result = await locate_device("aa:bb:cc:dd:ee:ff", enabled=True, ctx=mock_ctx)
    assert "enabled" in result
    mock_api_client.post_cmd.assert_called_once_with(
        "devmgr", "set-locate", mac="aa:bb:cc:dd:ee:ff"
    )


@pytest.mark.asyncio
async def test_locate_device_off(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.devices import locate_device
    result = await locate_device("aa:bb:cc:dd:ee:ff", enabled=False, ctx=mock_ctx)
    assert "disabled" in result
    mock_api_client.post_cmd.assert_called_once_with(
        "devmgr", "unset-locate", mac="aa:bb:cc:dd:ee:ff"
    )
