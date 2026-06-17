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
async def test_list_wlans_enhanced(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {
            "_id": "wlan1",
            "name": "HomeWiFi",
            "enabled": True,
            "security": "wpapsk",
            "wpa3_support": True,
            "is_guest": False,
            "hide_ssid": False,
            "fast_roaming_enabled": True,
            "bss_transition": True,
            "wlan_band": "5g",
        }
    ]
    from udm_pro_mcp.tools.network import list_wlans
    result = await list_wlans(mock_ctx)
    assert "HomeWiFi" in result
    assert "WPA3" in result
    assert "11r" in result
    assert "11v" in result
    assert "5GHz" in result


@pytest.mark.asyncio
async def test_get_wlan_details(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {
            "_id": "wlan1",
            "name": "TestWiFi",
            "enabled": True,
            "security": "wpapsk",
            "wpa_mode": "wpa2",
            "wpa3_support": True,
            "pmf_mode": "optional",
            "fast_roaming_enabled": True,
            "bss_transition": True,
            "dtim_mode": "custom",
            "dtim_ng": 3,
            "dtim_na": 1,
            "uapsd_enabled": True,
            "mcastenhance_enabled": True,
            "proxy_arp": True,
            "l2_isolation": False,
            "hide_ssid": False,
            "wlan_band": "both",
            "minrssi_enabled": True,
            "minrssi": -70,
        }
    ]
    from udm_pro_mcp.tools.network import get_wlan_details
    result = await get_wlan_details("wlan1", mock_ctx)
    assert "TestWiFi" in result
    assert "optional" in result
    assert "802.11r Fast Roaming" in result
    assert "True" in result
    assert "-70" in result
    assert "[Security]" in result
    assert "[Roaming]" in result


@pytest.mark.asyncio
async def test_get_wlan_details_not_found(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = []
    from udm_pro_mcp.tools.network import get_wlan_details
    result = await get_wlan_details("nonexistent", mock_ctx)
    assert "not found" in result


@pytest.mark.asyncio
async def test_update_wlan(mock_ctx, mock_api_client):
    mock_api_client.put.return_value = {}
    from udm_pro_mcp.tools.network import update_wlan
    result = await update_wlan(
        "wlan1",
        bss_transition=True,
        fast_roaming_enabled=False,
        pmf_mode="optional",
        ctx=mock_ctx,
    )
    assert "updated" in result
    assert "bss_transition=True" in result
    assert "fast_roaming_enabled=False" in result
    assert "pmf_mode=optional" in result
    mock_api_client.put.assert_called_once_with(
        "rest/wlanconf/wlan1",
        {
            "bss_transition": True,
            "fast_roaming_enabled": False,
            "pmf_mode": "optional",
        },
    )


@pytest.mark.asyncio
async def test_update_wlan_no_changes(mock_ctx, mock_api_client):
    from udm_pro_mcp.tools.network import update_wlan
    result = await update_wlan("wlan1", ctx=mock_ctx)
    assert "No settings provided" in result
    mock_api_client.put.assert_not_called()


@pytest.mark.asyncio
async def test_update_wlan_multicast_maps_to_mcastenhance(mock_ctx, mock_api_client):
    mock_api_client.put.return_value = {}
    from udm_pro_mcp.tools.network import update_wlan
    await update_wlan("wlan1", multicast_enhance=True, ctx=mock_ctx)
    call_payload = mock_api_client.put.call_args[0][1]
    assert "mcastenhance_enabled" in call_payload
    assert call_payload["mcastenhance_enabled"] is True


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
