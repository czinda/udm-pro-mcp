"""Network configuration tools: networks, VLANs, WLANs, firewall, port forwarding."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ..models import (
    FirewallRuleSummary,
    NetworkSummary,
    PortForwardSummary,
    WLANSummary,
)
from ..server import AppContext, mcp


def _client(ctx: Context[ServerSession, AppContext]):
    return ctx.request_context.lifespan_context.client


# ---- Networks / VLANs ----


@mcp.tool()
async def list_networks(ctx: Context[ServerSession, AppContext]) -> str:
    """List all configured networks (LANs/VLANs)."""
    data = await _client(ctx).get("rest/networkconf")
    networks = [NetworkSummary.from_api(n) for n in data]
    if not networks:
        return "No networks configured."
    lines = [f"Networks ({len(networks)}):"]
    for n in networks:
        vlan = f" VLAN {n.vlan}" if n.vlan else ""
        dhcp = " DHCP" if n.dhcp_enabled else ""
        lines.append(f"- {n.name} | {n.purpose}{vlan} | {n.subnet}{dhcp} | id={n.id}")
    return "\n".join(lines)


@mcp.tool()
async def get_network_details(
    network_id: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Get full details for a specific network by its ID."""
    data = await _client(ctx).get(f"rest/networkconf/{network_id}")
    if not data:
        return f"Network {network_id} not found."
    n = data[0] if isinstance(data, list) else data
    important_keys = [
        "_id", "name", "purpose", "vlan", "ip_subnet", "dhcpd_enabled",
        "dhcpd_start", "dhcpd_stop", "dhcpd_leasetime", "dhcpd_dns_enabled",
        "domain_name", "enabled", "igmp_snooping", "dhcp_relay_enabled",
        "dhcpd_gateway_enabled", "dhcpd_gateway",
    ]
    lines = []
    for k in important_keys:
        if k in n:
            lines.append(f"{k}: {n[k]}")
    return "\n".join(lines) if lines else "No details available."


@mcp.tool()
async def create_network(
    name: str,
    purpose: str = "corporate",
    vlan: int | None = None,
    subnet: str | None = None,
    dhcp_enabled: bool = True,
    dhcp_start: str | None = None,
    dhcp_stop: str | None = None,
    ctx: Context[ServerSession, AppContext] = None,  # type: ignore[assignment]
) -> str:
    """Create a new network/VLAN.

    Args:
        name: Network name.
        purpose: 'corporate', 'guest', or 'vlan-only'.
        vlan: VLAN ID (optional).
        subnet: IP subnet in CIDR (e.g. '192.168.10.1/24').
        dhcp_enabled: Enable DHCP server.
        dhcp_start: DHCP range start IP.
        dhcp_stop: DHCP range end IP.
    """
    payload: dict[str, Any] = {
        "name": name,
        "purpose": purpose,
        "dhcpd_enabled": dhcp_enabled,
    }
    if vlan is not None:
        payload["vlan"] = vlan
        payload["vlan_enabled"] = True
    if subnet:
        payload["ip_subnet"] = subnet
    if dhcp_start:
        payload["dhcpd_start"] = dhcp_start
    if dhcp_stop:
        payload["dhcpd_stop"] = dhcp_stop

    data = await _client(ctx).post("rest/networkconf", payload)
    new_id = ""
    if isinstance(data, list) and data:
        new_id = data[0].get("_id", "")
    elif isinstance(data, dict):
        new_id = data.get("_id", "")
    return f"Network '{name}' created (id={new_id})."


@mcp.tool()
async def delete_network(
    network_id: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Delete a network by its ID. Use list_networks to find the ID."""
    await _client(ctx).delete(f"rest/networkconf/{network_id}")
    return f"Network {network_id} deleted."


# ---- WLANs ----


@mcp.tool()
async def list_wlans(ctx: Context[ServerSession, AppContext]) -> str:
    """List all configured wireless networks (SSIDs)."""
    data = await _client(ctx).get("rest/wlanconf")
    wlans = [WLANSummary.from_api(w) for w in data]
    if not wlans:
        return "No WLANs configured."
    lines = [f"WLANs ({len(wlans)}):"]
    for w in wlans:
        status = "enabled" if w.enabled else "disabled"
        sec = w.security
        if w.wpa3_support:
            sec += "+WPA3"
        band = {"both": "2.4/5", "2g": "2.4", "5g": "5"}.get(w.wlan_band, w.wlan_band)
        roaming = []
        if w.fast_roaming:
            roaming.append("11r")
        if w.bss_transition:
            roaming.append("11v")
        roaming_str = f" [{'/'.join(roaming)}]" if roaming else ""
        tags = []
        if w.is_guest:
            tags.append("guest")
        if w.hide_ssid:
            tags.append("hidden")
        tags_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(
            f"- {w.name} | {sec} | {band}GHz | {status}"
            f"{roaming_str}{tags_str} | id={w.id}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_wlan_details(
    wlan_id: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Get full configuration details for a wireless network by its ID."""
    data = await _client(ctx).get(f"rest/wlanconf/{wlan_id}")
    if not data:
        return f"WLAN {wlan_id} not found."
    w = data[0] if isinstance(data, list) else data
    sections: dict[str, list[tuple[str, Any]]] = {
        "Basic": [
            ("Name", w.get("name")),
            ("Enabled", w.get("enabled")),
            ("SSID", w.get("name")),
            ("Hidden", w.get("hide_ssid")),
            ("Band", w.get("wlan_band", "both")),
            ("Network ID", w.get("networkconf_id")),
            ("AP Groups", w.get("ap_group_ids")),
            ("Is Guest", w.get("is_guest")),
        ],
        "Security": [
            ("Security", w.get("security")),
            ("WPA Mode", w.get("wpa_mode")),
            ("WPA3 Support", w.get("wpa3_support")),
            ("WPA3 Transition", w.get("wpa3_transition")),
            ("PMF Mode", w.get("pmf_mode")),
            ("Group Rekey (s)", w.get("group_rekey")),
        ],
        "Roaming": [
            ("802.11r Fast Roaming", w.get("fast_roaming_enabled")),
            ("802.11v BSS Transition", w.get("bss_transition")),
        ],
        "Performance": [
            ("DTIM Mode", w.get("dtim_mode")),
            ("DTIM 2.4GHz", w.get("dtim_ng")),
            ("DTIM 5GHz", w.get("dtim_na")),
            ("DTIM 6GHz", w.get("dtim_6e")),
            ("UAPSD", w.get("uapsd_enabled")),
        ],
        "Multicast & Isolation": [
            ("Multicast Enhance", w.get("mcastenhance_enabled",
                                        w.get("multicast_enhance"))),
            ("Proxy ARP", w.get("proxy_arp")),
            ("L2 Isolation", w.get("l2_isolation")),
        ],
        "Min RSSI": [
            ("Min RSSI Enabled", w.get("minrssi_enabled")),
            ("Min RSSI (dBm)", w.get("minrssi")),
        ],
        "Min Data Rate": [
            ("2.4GHz Enabled", w.get("minrate_ng_enabled")),
            ("2.4GHz Rate (kbps)", w.get("minrate_ng_data_rate_kbps")),
            ("5GHz Enabled", w.get("minrate_na_enabled")),
            ("5GHz Rate (kbps)", w.get("minrate_na_data_rate_kbps")),
        ],
        "MAC Filter": [
            ("MAC Filter", w.get("mac_filter_enabled")),
            ("MAC Filter Policy", w.get("mac_filter_policy")),
        ],
    }
    lines = []
    for section, fields in sections.items():
        visible = [(k, v) for k, v in fields if v is not None]
        if visible:
            lines.append(f"\n[{section}]")
            for k, v in visible:
                lines.append(f"  {k}: {v}")
    return "\n".join(lines).strip() if lines else "No details available."


@mcp.tool()
async def enable_wlan(
    wlan_id: str,
    enabled: bool = True,
    ctx: Context[ServerSession, AppContext] = None,  # type: ignore[assignment]
) -> str:
    """Enable or disable a wireless network by its ID."""
    await _client(ctx).put(f"rest/wlanconf/{wlan_id}", {"enabled": enabled})
    action = "enabled" if enabled else "disabled"
    return f"WLAN {wlan_id} {action}."


@mcp.tool()
async def update_wlan(
    wlan_id: str,
    security: str | None = None,
    wpa_mode: str | None = None,
    wpa3_support: bool | None = None,
    wpa3_transition: bool | None = None,
    pmf_mode: str | None = None,
    fast_roaming_enabled: bool | None = None,
    bss_transition: bool | None = None,
    dtim_mode: str | None = None,
    dtim_ng: int | None = None,
    dtim_na: int | None = None,
    dtim_6e: int | None = None,
    uapsd_enabled: bool | None = None,
    multicast_enhance: bool | None = None,
    proxy_arp: bool | None = None,
    l2_isolation: bool | None = None,
    hide_ssid: bool | None = None,
    group_rekey: int | None = None,
    minrssi_enabled: bool | None = None,
    minrssi: int | None = None,
    minrate_ng_enabled: bool | None = None,
    minrate_na_enabled: bool | None = None,
    minrate_ng_data_rate_kbps: int | None = None,
    minrate_na_data_rate_kbps: int | None = None,
    wlan_band: str | None = None,
    ctx: Context[ServerSession, AppContext] = None,  # type: ignore[assignment]
) -> str:
    """Update wireless network settings.

    Args:
        wlan_id: WLAN ID (from list_wlans).
        security: Security type — 'wpapsk', 'wpaeap', or 'open'.
        wpa_mode: WPA version — 'wpa2', 'wpa3'.
        wpa3_support: Enable WPA3.
        wpa3_transition: Enable WPA3/WPA2 transition mode.
        pmf_mode: Protected Management Frames — 'disabled', 'optional', 'required'.
        fast_roaming_enabled: 802.11r Fast BSS Transition.
        bss_transition: 802.11v BSS Transition Management.
        dtim_mode: DTIM mode — 'default' or 'custom'.
        dtim_ng: DTIM period for 2.4GHz radio.
        dtim_na: DTIM period for 5GHz radio.
        dtim_6e: DTIM period for 6GHz radio.
        uapsd_enabled: Unscheduled Automatic Power Save Delivery.
        multicast_enhance: Multicast enhancement (IGMPv3 → unicast).
        proxy_arp: Proxy ARP to reduce broadcast.
        l2_isolation: Layer 2 client isolation.
        hide_ssid: Hide SSID from broadcast.
        group_rekey: Group key rekey interval in seconds.
        minrssi_enabled: Enable minimum RSSI enforcement.
        minrssi: Minimum RSSI threshold in dBm (negative, e.g. -70).
        minrate_ng_enabled: Enable minimum data rate for 2.4GHz.
        minrate_na_enabled: Enable minimum data rate for 5GHz.
        minrate_ng_data_rate_kbps: Minimum data rate for 2.4GHz in kbps.
        minrate_na_data_rate_kbps: Minimum data rate for 5GHz in kbps.
        wlan_band: Band selection — '2g', '5g', or 'both'.
    """
    field_map = {
        "security": security,
        "wpa_mode": wpa_mode,
        "wpa3_support": wpa3_support,
        "wpa3_transition": wpa3_transition,
        "pmf_mode": pmf_mode,
        "fast_roaming_enabled": fast_roaming_enabled,
        "bss_transition": bss_transition,
        "dtim_mode": dtim_mode,
        "dtim_ng": dtim_ng,
        "dtim_na": dtim_na,
        "dtim_6e": dtim_6e,
        "uapsd_enabled": uapsd_enabled,
        "mcastenhance_enabled": multicast_enhance,
        "proxy_arp": proxy_arp,
        "l2_isolation": l2_isolation,
        "hide_ssid": hide_ssid,
        "group_rekey": group_rekey,
        "minrssi_enabled": minrssi_enabled,
        "minrssi": minrssi,
        "minrate_ng_enabled": minrate_ng_enabled,
        "minrate_na_enabled": minrate_na_enabled,
        "minrate_ng_data_rate_kbps": minrate_ng_data_rate_kbps,
        "minrate_na_data_rate_kbps": minrate_na_data_rate_kbps,
        "wlan_band": wlan_band,
    }
    payload = {k: v for k, v in field_map.items() if v is not None}
    if not payload:
        return "No settings provided to update."
    await _client(ctx).put(f"rest/wlanconf/{wlan_id}", payload)
    changed = ", ".join(f"{k}={v}" for k, v in payload.items())
    return f"WLAN {wlan_id} updated: {changed}"


@mcp.tool()
async def update_wlan_password(
    wlan_id: str, password: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Change the password for a wireless network."""
    if len(password) < 8:
        return "Error: WiFi password must be at least 8 characters."
    await _client(ctx).put(f"rest/wlanconf/{wlan_id}", {"x_passphrase": password})
    return f"WLAN {wlan_id} password updated."


# ---- Firewall Rules ----


@mcp.tool()
async def list_firewall_rules(ctx: Context[ServerSession, AppContext]) -> str:
    """List all firewall rules."""
    data = await _client(ctx).get("rest/firewallrule")
    rules = [FirewallRuleSummary.from_api(r) for r in data]
    if not rules:
        return "No firewall rules configured."
    lines = [f"Firewall rules ({len(rules)}):"]
    for r in rules:
        status = "enabled" if r.enabled else "disabled"
        lines.append(
            f"- [{r.ruleset}] #{r.rule_index} {r.name} | "
            f"{r.action} | {r.protocol} | {status} | id={r.id}"
        )
    return "\n".join(lines)


@mcp.tool()
async def create_firewall_rule(
    name: str,
    action: str = "drop",
    ruleset: str = "LAN_IN",
    protocol: str = "all",
    src_network_id: str | None = None,
    src_address: str | None = None,
    dst_network_id: str | None = None,
    dst_address: str | None = None,
    dst_port: str | None = None,
    rule_index: int = 2000,
    enabled: bool = True,
    ctx: Context[ServerSession, AppContext] = None,  # type: ignore[assignment]
) -> str:
    """Create a new firewall rule.

    Args:
        name: Rule name.
        action: 'accept', 'drop', or 'reject'.
        ruleset: 'LAN_IN', 'LAN_OUT', 'LAN_LOCAL', 'WAN_IN', 'WAN_OUT', etc.
        protocol: 'all', 'tcp', 'udp', 'tcp_udp', 'icmp'.
        src_network_id: Source network ID (from list_networks).
        src_address: Source IP/CIDR.
        dst_network_id: Destination network ID.
        dst_address: Destination IP/CIDR.
        dst_port: Destination port or range.
        rule_index: Rule priority (lower = evaluated first, default 2000).
        enabled: Whether the rule is active.
    """
    payload: dict[str, Any] = {
        "name": name,
        "action": action,
        "ruleset": ruleset,
        "protocol": protocol,
        "protocol_match_excepted": False,
        "rule_index": rule_index,
        "enabled": enabled,
    }
    if src_network_id:
        payload["src_networkconf_id"] = src_network_id
        payload["src_networkconf_type"] = "NETv4"
    if src_address:
        payload["src_address"] = src_address
    if dst_network_id:
        payload["dst_networkconf_id"] = dst_network_id
        payload["dst_networkconf_type"] = "NETv4"
    if dst_address:
        payload["dst_address"] = dst_address
    if dst_port:
        payload["dst_port"] = dst_port

    data = await _client(ctx).post("rest/firewallrule", payload)
    new_id = ""
    if isinstance(data, list) and data:
        new_id = data[0].get("_id", "")
    elif isinstance(data, dict):
        new_id = data.get("_id", "")
    return f"Firewall rule '{name}' created (id={new_id})."


@mcp.tool()
async def delete_firewall_rule(
    rule_id: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Delete a firewall rule by its ID."""
    await _client(ctx).delete(f"rest/firewallrule/{rule_id}")
    return f"Firewall rule {rule_id} deleted."


# ---- Port Forwarding ----


@mcp.tool()
async def list_port_forwards(ctx: Context[ServerSession, AppContext]) -> str:
    """List all port forwarding rules."""
    data = await _client(ctx).get("rest/portforward")
    fwds = [PortForwardSummary.from_api(f) for f in data]
    if not fwds:
        return "No port forwarding rules configured."
    lines = [f"Port forwards ({len(fwds)}):"]
    for f in fwds:
        status = "enabled" if f.enabled else "disabled"
        lines.append(
            f"- {f.name} | :{f.dst_port} → {f.fwd}:{f.fwd_port} | "
            f"{f.proto} | {status} | id={f.id}"
        )
    return "\n".join(lines)


@mcp.tool()
async def create_port_forward(
    name: str,
    dst_port: str,
    fwd: str,
    fwd_port: str,
    proto: str = "tcp_udp",
    enabled: bool = True,
    ctx: Context[ServerSession, AppContext] = None,  # type: ignore[assignment]
) -> str:
    """Create a port forwarding rule.

    Args:
        name: Rule name.
        dst_port: External port (or range like '8080-8090').
        fwd: Internal destination IP address.
        fwd_port: Internal destination port.
        proto: Protocol — 'tcp', 'udp', or 'tcp_udp'.
        enabled: Whether the rule is active.
    """
    payload = {
        "name": name,
        "dst_port": dst_port,
        "fwd": fwd,
        "fwd_port": fwd_port,
        "proto": proto,
        "enabled": enabled,
        "src": "any",
        "pfwd_interface": "wan",
    }
    data = await _client(ctx).post("rest/portforward", payload)
    new_id = ""
    if isinstance(data, list) and data:
        new_id = data[0].get("_id", "")
    elif isinstance(data, dict):
        new_id = data.get("_id", "")
    return f"Port forward '{name}' created (id={new_id})."


@mcp.tool()
async def delete_port_forward(
    rule_id: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Delete a port forwarding rule by its ID."""
    await _client(ctx).delete(f"rest/portforward/{rule_id}")
    return f"Port forward {rule_id} deleted."
