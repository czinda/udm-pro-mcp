"""Tests for network configuration tools."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_list_networks(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {
            "_id": "net1",
            "name": "Default",
            "purpose": "corporate",
            "ip_subnet": "192.168.1.0/24",
            "dhcpd_enabled": True,
        },
        {
            "_id": "net2",
            "name": "IoT",
            "purpose": "corporate",
            "vlan": 20,
            "ip_subnet": "192.168.20.0/24",
            "dhcpd_enabled": True,
        },
    ]
    from udm_pro_mcp.tools.network import list_networks
    result = await list_networks(mock_ctx)
    assert "Default" in result
    assert "IoT" in result
    assert "VLAN 20" in result


@pytest.mark.asyncio
async def test_list_networks_empty(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = []
    from udm_pro_mcp.tools.network import list_networks
    result = await list_networks(mock_ctx)
    assert result == "No networks configured."


@pytest.mark.asyncio
async def test_list_wlans(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {
            "_id": "wlan1",
            "name": "HomeWiFi",
            "enabled": True,
            "security": "wpapsk",
            "is_guest": False,
            "hide_ssid": False,
        }
    ]
    from udm_pro_mcp.tools.network import list_wlans
    result = await list_wlans(mock_ctx)
    assert "HomeWiFi" in result
    assert "enabled" in result


@pytest.mark.asyncio
async def test_list_firewall_rules(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {
            "_id": "rule1",
            "name": "Block IoT to LAN",
            "ruleset": "LAN_IN",
            "rule_index": 2000,
            "action": "drop",
            "enabled": True,
            "protocol": "all",
        }
    ]
    from udm_pro_mcp.tools.network import list_firewall_rules
    result = await list_firewall_rules(mock_ctx)
    assert "Block IoT to LAN" in result
    assert "drop" in result


@pytest.mark.asyncio
async def test_create_network(mock_ctx, mock_api_client):
    mock_api_client.post.return_value = [{"_id": "new-net-id"}]
    from udm_pro_mcp.tools.network import create_network
    result = await create_network(
        name="Guest",
        purpose="guest",
        vlan=30,
        subnet="192.168.30.1/24",
        ctx=mock_ctx,
    )
    assert "Guest" in result
    assert "new-net-id" in result


@pytest.mark.asyncio
async def test_list_port_forwards(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {
            "_id": "pf1",
            "name": "Web Server",
            "enabled": True,
            "dst_port": "80",
            "fwd": "192.168.1.100",
            "fwd_port": "8080",
            "proto": "tcp",
        }
    ]
    from udm_pro_mcp.tools.network import list_port_forwards
    result = await list_port_forwards(mock_ctx)
    assert "Web Server" in result
    assert "192.168.1.100" in result
