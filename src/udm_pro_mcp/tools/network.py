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
        guest = " [guest]" if w.is_guest else ""
        hidden = " [hidden]" if w.hide_ssid else ""
        lines.append(f"- {w.name} | {w.security} | {status}{guest}{hidden} | id={w.id}")
    return "\n".join(lines)


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
    dst_network_id: str | None = None,
    dst_address: str | None = None,
    dst_port: str | None = None,
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
        dst_network_id: Destination network ID.
        dst_address: Destination IP/CIDR.
        dst_port: Destination port or range.
        enabled: Whether the rule is active.
    """
    payload: dict[str, Any] = {
        "name": name,
        "action": action,
        "ruleset": ruleset,
        "protocol": protocol,
        "enabled": enabled,
    }
    if src_network_id:
        payload["src_networkconf_id"] = src_network_id
        payload["src_networkconf_type"] = "NETv4"
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
