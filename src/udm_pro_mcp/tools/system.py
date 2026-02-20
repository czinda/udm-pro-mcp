"""System operations tools: reboot, backups, alarms, DDNS."""

from __future__ import annotations

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ..server import AppContext, mcp


def _client(ctx: Context[ServerSession, AppContext]):
    return ctx.request_context.lifespan_context.client


@mcp.tool()
async def reboot_udm(ctx: Context[ServerSession, AppContext]) -> str:
    """Reboot the UDM Pro gateway itself."""
    # Get the UDM's MAC first
    data = await _client(ctx).get("stat/device")
    if not data:
        return "No gateway device found."
    gw = next(
        (d for d in data if d.get("type") == "ugw" or d.get("type") == "udm"),
        data[0],
    )
    mac = gw["mac"]
    await _client(ctx).post_cmd("devmgr", "restart", mac=mac)
    return f"Reboot command sent to UDM Pro ({mac}). The device will restart."


@mcp.tool()
async def create_backup(ctx: Context[ServerSession, AppContext]) -> str:
    """Create a controller backup."""
    await _client(ctx).post_cmd("backup", "backup")
    return "Backup initiated. Use list_backups to see available backups."


@mcp.tool()
async def list_backups(ctx: Context[ServerSession, AppContext]) -> str:
    """List available controller backups."""
    data = await _client(ctx).post_cmd("backup", "list-backups")
    if not data:
        return "No backups found."
    lines = [f"Backups ({len(data)}):"]
    for b in data:
        name = b.get("filename", "unknown")
        size = b.get("size", 0)
        time_val = b.get("datetime", b.get("time", ""))
        lines.append(f"- {name} | {size} bytes | {time_val}")
    return "\n".join(lines)


@mcp.tool()
async def archive_all_alarms(ctx: Context[ServerSession, AppContext]) -> str:
    """Archive (acknowledge) all active alarms."""
    await _client(ctx).post_cmd("evtmgr", "archive-all-alarms")
    return "All alarms have been archived."


@mcp.tool()
async def get_ddns_status(ctx: Context[ServerSession, AppContext]) -> str:
    """Get dynamic DNS configuration and status."""
    data = await _client(ctx).get("rest/setting/dynamicdns")
    if not data:
        return "No DDNS configuration found."
    entry = data[0] if isinstance(data, list) else data
    fields = [
        ("Enabled", entry.get("enabled")),
        ("Service", entry.get("service")),
        ("Hostname", entry.get("host_name")),
        ("Server", entry.get("server")),
        ("Login", entry.get("login")),
        ("Interface", entry.get("interface")),
    ]
    return "DDNS Config:\n" + "\n".join(
        f"  {k}: {v}" for k, v in fields if v is not None
    )


@mcp.tool()
async def get_syslog(
    count: int = 100,
    ctx: Context[ServerSession, AppContext] = None,  # type: ignore[assignment]
) -> str:
    """Get recent system log entries from the controller."""
    data = await _client(ctx).get(f"stat/event?_limit={count}&_sort=-time")
    if not data:
        return "No syslog entries."
    lines = [f"Recent syslog ({len(data)} entries):"]
    for entry in data:
        sub = entry.get("subsystem", "")
        key = entry.get("key", "")
        msg = entry.get("msg", "")
        lines.append(f"- [{sub}] {key}: {msg}")
    return "\n".join(lines)
