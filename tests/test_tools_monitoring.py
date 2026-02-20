"""Tests for monitoring tools."""

from __future__ import annotations

import pytest

from udm_pro_mcp.tools.monitoring import _human_bytes, _human_duration


def test_human_bytes():
    assert _human_bytes(0) == "0.0 B"
    assert _human_bytes(512) == "512.0 B"
    assert _human_bytes(1024) == "1.0 KB"
    assert _human_bytes(1048576) == "1.0 MB"
    assert _human_bytes(1073741824) == "1.0 GB"


def test_human_duration():
    assert _human_duration(0) == "0s"
    assert _human_duration(30) == "30s"
    assert _human_duration(90) == "1m 30s"
    assert _human_duration(3661) == "1h 1m"
    assert _human_duration(90061) == "1d 1h 1m"


@pytest.mark.asyncio
async def test_get_site_health(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {"subsystem": "wan", "status": "ok", "wan_ip": "1.2.3.4"},
        {"subsystem": "lan", "status": "ok", "num_user": 15},
        {"subsystem": "wlan", "status": "ok", "num_user": 8, "num_ap": 3},
    ]
    from udm_pro_mcp.tools.monitoring import get_site_health
    result = await get_site_health(mock_ctx)
    assert "wan: ok" in result
    assert "1.2.3.4" in result
    assert "lan: ok" in result
    assert "wlan: ok" in result


@pytest.mark.asyncio
async def test_list_active_clients_empty(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = []
    from udm_pro_mcp.tools.monitoring import list_active_clients
    result = await list_active_clients(mock_ctx)
    assert result == "No active clients."


@pytest.mark.asyncio
async def test_list_active_clients(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {
            "mac": "aa:bb:cc:dd:ee:ff",
            "hostname": "laptop",
            "ip": "192.168.1.50",
            "is_wired": True,
            "tx_bytes": 1024,
            "rx_bytes": 2048,
        }
    ]
    from udm_pro_mcp.tools.monitoring import list_active_clients
    result = await list_active_clients(mock_ctx)
    assert "laptop" in result
    assert "192.168.1.50" in result
    assert "wired" in result


@pytest.mark.asyncio
async def test_list_alarms_no_active(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {"_id": "1", "key": "test", "msg": "old alarm", "time": 0, "archived": True}
    ]
    from udm_pro_mcp.tools.monitoring import list_alarms
    result = await list_alarms(mock_ctx)
    assert result == "No active alarms."
