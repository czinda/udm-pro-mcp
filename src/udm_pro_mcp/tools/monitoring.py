"""Monitoring tools: health, clients, DPI, events, traffic."""

from __future__ import annotations

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ..models import AlarmSummary, ClientSummary, EventSummary
from ..server import AppContext, mcp


def _client(ctx: Context[ServerSession, AppContext]):
    return ctx.request_context.lifespan_context.client


@mcp.tool()
async def get_site_health(ctx: Context[ServerSession, AppContext]) -> str:
    """Get overall site health status including subsystem health (WAN, LAN, WLAN)."""
    data = await _client(ctx).get("stat/health")
    lines = []
    for sub in data:
        name = sub.get("subsystem", "unknown")
        status = sub.get("status", "unknown")
        extras = []
        if "num_user" in sub:
            extras.append(f"users={sub['num_user']}")
        if "num_ap" in sub:
            extras.append(f"APs={sub['num_ap']}")
        if "tx_bytes-r" in sub:
            extras.append(f"tx={_human_bytes(sub['tx_bytes-r'])}/s")
        if "rx_bytes-r" in sub:
            extras.append(f"rx={_human_bytes(sub['rx_bytes-r'])}/s")
        if "wan_ip" in sub:
            extras.append(f"ip={sub['wan_ip']}")
        detail = f" ({', '.join(extras)})" if extras else ""
        lines.append(f"- {name}: {status}{detail}")
    return "Site Health:\n" + "\n".join(lines)


@mcp.tool()
async def list_active_clients(ctx: Context[ServerSession, AppContext]) -> str:
    """List all currently connected clients with key details."""
    data = await _client(ctx).get("stat/sta")
    clients = [ClientSummary.from_api(c) for c in data]
    if not clients:
        return "No active clients."
    lines = [f"Active clients ({len(clients)}):"]
    for c in sorted(clients, key=lambda x: x.hostname.lower()):
        conn = "wired" if c.is_wired else f"wifi (signal {c.signal})"
        lines.append(f"- {c.hostname or c.mac} | {c.ip} | {conn} | "
                      f"tx={_human_bytes(c.tx_bytes)} rx={_human_bytes(c.rx_bytes)}")
    return "\n".join(lines)


@mcp.tool()
async def get_client_details(
    mac: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Get detailed information about a specific client by MAC address."""
    mac = mac.lower().replace("-", ":")
    data = await _client(ctx).get(f"stat/sta/{mac}")
    if not data:
        return f"No active client found with MAC {mac}."
    c = data[0]
    fields = [
        ("Hostname", c.get("hostname", c.get("name", "unknown"))),
        ("MAC", c.get("mac")),
        ("IP", c.get("ip")),
        ("Wired", c.get("is_wired")),
        ("Network", c.get("network")),
        ("VLAN", c.get("vlan")),
        ("Signal", c.get("signal")),
        ("Satisfaction", c.get("satisfaction")),
        ("Channel", c.get("channel")),
        ("Radio", c.get("radio")),
        ("TX Rate", c.get("tx_rate")),
        ("RX Rate", c.get("rx_rate")),
        ("TX Bytes", _human_bytes(c.get("tx_bytes", 0))),
        ("RX Bytes", _human_bytes(c.get("rx_bytes", 0))),
        ("Uptime", _human_duration(c.get("uptime", 0))),
        ("Switch Port", c.get("sw_port")),
        ("AP Name", c.get("ap_name")),
        ("OUI", c.get("oui")),
    ]
    lines = [f"{k}: {v}" for k, v in fields if v is not None]
    return "\n".join(lines)


@mcp.tool()
async def list_all_known_clients(ctx: Context[ServerSession, AppContext]) -> str:
    """List all clients ever seen by the controller (active and historical)."""
    data = await _client(ctx).get("rest/user")
    if not data:
        return "No known clients."
    lines = [f"Known clients ({len(data)}):"]
    for c in data:
        name = c.get("name", c.get("hostname", c.get("mac", "unknown")))
        mac = c.get("mac", "")
        note = c.get("note", "")
        extra = f" — {note}" if note else ""
        lines.append(f"- {name} ({mac}){extra}")
    return "\n".join(lines)


@mcp.tool()
async def get_dpi_stats(ctx: Context[ServerSession, AppContext]) -> str:
    """Get Deep Packet Inspection stats showing application usage breakdown."""
    data = await _client(ctx).get("stat/dpi")
    if not data:
        return "No DPI data available."
    lines = ["DPI Application Stats:"]
    for entry in data:
        cat = entry.get("cat_name", entry.get("cat", "unknown"))
        app = entry.get("app_name", entry.get("app", ""))
        tx = _human_bytes(entry.get("tx_bytes", 0))
        rx = _human_bytes(entry.get("rx_bytes", 0))
        label = f"{cat}/{app}" if app else cat
        lines.append(f"- {label}: tx={tx} rx={rx}")
    return "\n".join(lines)


@mcp.tool()
async def list_events(
    count: int = 50, ctx: Context[ServerSession, AppContext] = None  # type: ignore[assignment]
) -> str:
    """List recent controller events (default last 50)."""
    data = await _client(ctx).get(f"stat/event?_limit={count}")
    events = [EventSummary.from_api(e) for e in data]
    if not events:
        return "No recent events."
    lines = [f"Recent events ({len(events)}):"]
    for e in events:
        lines.append(f"- [{e.subsystem}] {e.key}: {e.msg}")
    return "\n".join(lines)


@mcp.tool()
async def list_alarms(ctx: Context[ServerSession, AppContext]) -> str:
    """List all unarchived alarms."""
    data = await _client(ctx).get("list/alarm")
    alarms = [AlarmSummary.from_api(a) for a in data]
    active = [a for a in alarms if not a.archived]
    if not active:
        return "No active alarms."
    lines = [f"Active alarms ({len(active)}):"]
    for a in active:
        lines.append(f"- [{a.key}] {a.msg}")
    return "\n".join(lines)


@mcp.tool()
async def get_traffic_report(
    interval: str = "hourly",
    attrs: str = "bytes,num_sta",
    ctx: Context[ServerSession, AppContext] = None,  # type: ignore[assignment]
) -> str:
    """Get traffic statistics report. interval: '5minutes', 'hourly', 'daily'."""
    data = await _client(ctx).post("stat/report/site." + interval, {
        "attrs": attrs.split(","),
    })
    if not data:
        return "No traffic data."
    lines = [f"Traffic report ({interval}), last {len(data)} entries:"]
    for entry in data[:24]:  # cap to keep output manageable
        t = entry.get("time", "")
        wan_tx = _human_bytes(entry.get("wan-tx_bytes", 0))
        wan_rx = _human_bytes(entry.get("wan-rx_bytes", 0))
        users = entry.get("num_sta", "?")
        lines.append(f"- {t}: wan_tx={wan_tx} wan_rx={wan_rx} users={users}")
    return "\n".join(lines)


@mcp.tool()
async def get_wan_info(ctx: Context[ServerSession, AppContext]) -> str:
    """Get WAN connection details including IP, ISP, latency."""
    health = await _client(ctx).get("stat/health")
    wan = next((s for s in health if s.get("subsystem") == "wan"), None)
    if not wan:
        return "WAN subsystem not found."
    fields = [
        ("Status", wan.get("status")),
        ("WAN IP", wan.get("wan_ip")),
        ("Gateway", wan.get("gw_name")),
        ("ISP", wan.get("isp_name")),
        ("Latency", f"{wan.get('latency', '?')} ms"),
        ("Download", f"{_human_bytes(wan.get('tx_bytes-r', 0))}/s"),
        ("Upload", f"{_human_bytes(wan.get('rx_bytes-r', 0))}/s"),
        ("Uptime", _human_duration(wan.get("gw_system-stats", {}).get("uptime", 0)
                                    if isinstance(wan.get("gw_system-stats"), dict) else 0)),
    ]
    return "WAN Info:\n" + "\n".join(f"  {k}: {v}" for k, v in fields if v is not None)


@mcp.tool()
async def get_system_info(ctx: Context[ServerSession, AppContext]) -> str:
    """Get UDM Pro system information (firmware, CPU, memory, temps)."""
    data = await _client(ctx).get("stat/device")
    if not data:
        return "No devices found."
    udm = data[0]  # UDM Pro is typically the first device
    sys_stats = udm.get("system-stats", {})
    temps = udm.get("temperatures", [])
    fields = [
        ("Name", udm.get("name", udm.get("hostname"))),
        ("Model", udm.get("model")),
        ("Firmware", udm.get("version")),
        ("Uptime", _human_duration(udm.get("uptime", 0))),
        ("CPU", f"{sys_stats.get('cpu', '?')}%"),
        ("Memory", f"{sys_stats.get('mem', '?')}%"),
    ]
    for t in temps:
        fields.append((t.get("name", "Temp"), f"{t.get('value', '?')}°C"))
    return "System Info:\n" + "\n".join(f"  {k}: {v}" for k, v in fields)


@mcp.tool()
async def get_client_history(
    mac: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Get historical connection data for a specific client."""
    mac = mac.lower().replace("-", ":")
    data = await _client(ctx).get(f"stat/user/{mac}")
    if not data:
        return f"No history found for {mac}."
    c = data[0] if isinstance(data, list) else data
    fields = [
        ("Name", c.get("name", c.get("hostname"))),
        ("MAC", c.get("mac")),
        ("First Seen", c.get("first_seen")),
        ("Last Seen", c.get("last_seen")),
        ("Fixed IP", c.get("fixed_ip")),
        ("Note", c.get("note")),
        ("Blocked", c.get("blocked")),
        ("Total TX", _human_bytes(c.get("tx_bytes", 0))),
        ("Total RX", _human_bytes(c.get("rx_bytes", 0))),
    ]
    return "\n".join(f"{k}: {v}" for k, v in fields if v is not None)


@mcp.tool()
async def get_isp_metrics(ctx: Context[ServerSession, AppContext]) -> str:
    """Get ISP performance metrics including latency and packet loss."""
    health = await _client(ctx).get("stat/health")
    wan = next((s for s in health if s.get("subsystem") == "wan"), None)
    if not wan:
        return "WAN subsystem not found."
    fields = [
        ("ISP", wan.get("isp_name", "unknown")),
        ("Latency", f"{wan.get('latency', '?')} ms"),
        ("Packet Loss (WAN)", wan.get("drops")),
        ("Uptime", wan.get("uptime")),
        ("TX Rate", f"{_human_bytes(wan.get('tx_bytes-r', 0))}/s"),
        ("RX Rate", f"{_human_bytes(wan.get('rx_bytes-r', 0))}/s"),
        ("xput_down", wan.get("xput_down")),
        ("xput_up", wan.get("xput_up")),
        ("Speedtest Last Run", wan.get("speedtest_lastrun")),
    ]
    return "ISP Metrics:\n" + "\n".join(f"  {k}: {v}" for k, v in fields if v is not None)


# ---- helpers ----

def _human_bytes(n: int | float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _human_duration(seconds: int | float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours < 24:
        return f"{hours}h {minutes}m"
    days = hours // 24
    hours = hours % 24
    return f"{days}d {hours}h {minutes}m"
