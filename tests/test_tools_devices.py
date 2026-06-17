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
async def test_get_device_details_with_radios(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {
            "mac": "aa:bb:cc:00:11:22",
            "name": "Living Room AP",
            "model": "U7PIW",
            "type": "uap",
            "ip": "192.168.1.51",
            "version": "8.6.11",
            "adopted": True,
            "state": 1,
            "uptime": 3600,
            "num_sta": 10,
            "system-stats": {"cpu": "5", "mem": "48"},
            "radio_table": [
                {"radio": "na", "channel": 149, "ht": "80", "tx_power": 23, "tx_power_mode": "high"},
                {"radio": "ng", "channel": 6, "ht": "20", "tx_power": 20, "tx_power_mode": "auto"},
            ],
            "radio_table_stats": [
                {"radio": "na", "channel": 149, "tx_power": 23, "num_sta": 7, "cu_total": 15},
                {"radio": "ng", "channel": 6, "tx_power": 20, "num_sta": 3, "cu_total": 25},
            ],
        }
    ]
    from udm_pro_mcp.tools.devices import get_device_details
    result = await get_device_details("aa:bb:cc:00:11:22", mock_ctx)
    assert "Living Room AP" in result
    assert "Radios:" in result
    assert "5GHz" in result
    assert "2.4GHz" in result
    assert "ch=149" in result
    assert "clients=7" in result


@pytest.mark.asyncio
async def test_rename_device(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [{"_id": "dev123", "mac": "aa:bb:cc:dd:ee:ff"}]
    mock_api_client.put.return_value = {}
    from udm_pro_mcp.tools.devices import rename_device
    result = await rename_device("AA:BB:CC:DD:EE:FF", "Living Room", mock_ctx)
    assert "renamed" in result
    assert "Living Room" in result
    mock_api_client.put.assert_called_once_with("rest/device/dev123", {"name": "Living Room"})


@pytest.mark.asyncio
async def test_rename_device_not_found(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = []
    from udm_pro_mcp.tools.devices import rename_device
    result = await rename_device("ff:ff:ff:ff:ff:ff", "Ghost", mock_ctx)
    assert "No device found" in result


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
