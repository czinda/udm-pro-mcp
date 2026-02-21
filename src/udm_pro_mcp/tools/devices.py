"""Device management tools: list, restart, upgrade, adopt, locate, speedtest."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ..models import DeviceSummary
from ..server import AppContext, mcp
from .monitoring import _human_bytes, _human_duration


def _client(ctx: Context[ServerSession, AppContext]):
    return ctx.request_context.lifespan_context.client


@mcp.tool()
async def list_devices(ctx: Context[ServerSession, AppContext]) -> str:
    """List all adopted UniFi devices (APs, switches, gateways)."""
    data = await _client(ctx).get("stat/device")
    devices = [DeviceSummary.from_api(d) for d in data]
    if not devices:
        return "No devices found."
    lines = [f"Devices ({len(devices)}):"]
    for d in devices:
        state_str = {1: "connected", 0: "disconnected", 2: "pending"}.get(
            d.state, f"state={d.state}"
        )
        lines.append(
            f"- {d.name or d.mac} | {d.model} | {d.type} | {d.ip} | "
            f"{state_str} | v{d.version} | clients={d.num_sta} | "
            f"uptime={_human_duration(d.uptime)}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_device_details(mac: str, ctx: Context[ServerSession, AppContext]) -> str:
    """Get detailed information about a specific device by MAC address."""
    mac = mac.lower().replace("-", ":")
    data = await _client(ctx).get(f"stat/device/{mac}")
    if not data:
        return f"No device found with MAC {mac}."
    d = data[0]
    sys_stats = d.get("system-stats", {})
    fields = [
        ("Name", d.get("name", d.get("hostname"))),
        ("MAC", d.get("mac")),
        ("Model", d.get("model")),
        ("Type", d.get("type")),
        ("IP", d.get("ip")),
        ("Firmware", d.get("version")),
        ("Adopted", d.get("adopted")),
        ("State", d.get("state")),
        ("Uptime", _human_duration(d.get("uptime", 0))),
        ("CPU", f"{sys_stats.get('cpu', '?')}%"),
        ("Memory", f"{sys_stats.get('mem', '?')}%"),
        ("Connected Clients", d.get("num_sta")),
        ("TX Bytes", _human_bytes(d.get("tx_bytes", 0))),
        ("RX Bytes", _human_bytes(d.get("rx_bytes", 0))),
        ("Satisfaction", d.get("satisfaction")),
        ("Upgradable", d.get("upgradable")),
        ("Upgrade To", d.get("upgrade_to_firmware")),
    ]
    # Port table for switches
    port_table = d.get("port_table")
    port_lines = []
    if port_table:
        for p in port_table:
            if p.get("up"):
                port_lines.append(
                    f"  Port {p.get('port_idx')}: {p.get('name', '')} "
                    f"speed={p.get('speed', '?')}Mbps "
                    f"tx={_human_bytes(p.get('tx_bytes', 0))} "
                    f"rx={_human_bytes(p.get('rx_bytes', 0))}"
                )
    result = "\n".join(f"{k}: {v}" for k, v in fields if v is not None)
    if port_lines:
        result += "\n\nActive Ports:\n" + "\n".join(port_lines)
    return result


@mcp.tool()
async def restart_device(mac: str, ctx: Context[ServerSession, AppContext]) -> str:
    """Restart (reboot) a specific UniFi device by MAC address."""
    mac = mac.lower().replace("-", ":")
    await _client(ctx).post_cmd("devmgr", "restart", mac=mac)
    return f"Restart command sent to device {mac}."


@mcp.tool()
async def upgrade_device(mac: str, ctx: Context[ServerSession, AppContext]) -> str:
    """Upgrade firmware on a specific device by MAC address."""
    mac = mac.lower().replace("-", ":")
    await _client(ctx).post_cmd("devmgr", "upgrade", mac=mac)
    return f"Firmware upgrade initiated for device {mac}."


@mcp.tool()
async def upgrade_all_devices(ctx: Context[ServerSession, AppContext]) -> str:
    """Upgrade firmware on all devices that have updates available."""
    data = await _client(ctx).get("stat/device")
    upgraded = []
    for d in data:
        if d.get("upgradable"):
            mac = d["mac"]
            await _client(ctx).post_cmd("devmgr", "upgrade", mac=mac)
            upgraded.append(d.get("name", mac))
    if not upgraded:
        return "No devices have firmware updates available."
    return f"Firmware upgrade initiated for: {', '.join(upgraded)}"


@mcp.tool()
async def adopt_device(mac: str, ctx: Context[ServerSession, AppContext]) -> str:
    """Adopt a new device by MAC address."""
    mac = mac.lower().replace("-", ":")
    await _client(ctx).post_cmd("devmgr", "adopt", mac=mac)
    return f"Adoption initiated for device {mac}."


@mcp.tool()
async def locate_device(
    mac: str,
    enabled: bool = True,
    ctx: Context[ServerSession, AppContext] = None,  # type: ignore[assignment]
) -> str:
    """Toggle the locate LED on a device. Set enabled=False to turn it off."""
    mac = mac.lower().replace("-", ":")
    await _client(ctx).post_cmd(
        "devmgr", "set-locate" if enabled else "unset-locate", mac=mac
    )
    action = "enabled" if enabled else "disabled"
    return f"Locate LED {action} on device {mac}."


@mcp.tool()
async def power_cycle_port(
    mac: str, port_idx: int, ctx: Context[ServerSession, AppContext]
) -> str:
    """Power cycle a specific port on a UniFi switch (PoE cycle)."""
    mac = mac.lower().replace("-", ":")
    await _client(ctx).post_cmd(
        "devmgr", "power-cycle", mac=mac, port_idx=port_idx
    )
    return f"Power cycle initiated on port {port_idx} of switch {mac}."


def _format_speedtest(status: dict) -> str:
    """Format speedtest_status fields into a human-readable result."""
    fields = [
        ("Download", f"{status.get('xput_download', '?')} Mbps"),
        ("Upload", f"{status.get('xput_upload', '?')} Mbps"),
        ("Latency", f"{status.get('latency', '?')} ms"),
        ("Server", status.get("server_desc")),
    ]
    return "Speed Test Results:\n" + "\n".join(
        f"  {k}: {v}" for k, v in fields if v is not None
    )


async def _find_udm(ctx: Context[ServerSession, AppContext]) -> dict | None:
    """Find the UDM/gateway device in the device list."""
    data = await _client(ctx).get("stat/device")
    for d in data:
        if d.get("type") in ("udm", "ugw"):
            return d
    return None


@mcp.tool()
async def run_speedtest(ctx: Context[ServerSession, AppContext]) -> str:
    """Run a speed test from the UDM Pro and return results."""
    await _client(ctx).post_cmd("devmgr", "speedtest")

    # Poll the UDM device for completed results
    for _ in range(30):
        await asyncio.sleep(2)
        udm = await _find_udm(ctx)
        if not udm:
            continue
        status = udm.get("speedtest-status", {})
        st_down = status.get("status_download", 0)
        st_up = status.get("status_upload", 0)
        # status 2 = finished for both download and upload
        if st_down == 2 and st_up == 2:
            return _format_speedtest(status)

    return "Speed test timed out waiting for results. Try get_speedtest_results later."


@mcp.tool()
async def get_speedtest_results(ctx: Context[ServerSession, AppContext]) -> str:
    """Get the latest speed test results."""
    # First try the live device status (most reliable)
    udm = await _find_udm(ctx)
    if udm:
        status = udm.get("speedtest-status", {})
        if status.get("xput_download"):
            return _format_speedtest(status)

    # Fall back to the historical archive
    data = await _client(ctx).get("stat/report/archive.speedtest")
    if not data:
        return "No speed test results available."
    latest = data[0]
    fields = [
        ("Download", f"{latest.get('xput_download', '?')} Mbps"),
        ("Upload", f"{latest.get('xput_upload', '?')} Mbps"),
        ("Latency", f"{latest.get('latency', '?')} ms"),
        ("Server", latest.get("server_desc")),
        ("Time", latest.get("time")),
    ]
    return "Latest Speed Test:\n" + "\n".join(
        f"  {k}: {v}" for k, v in fields if v is not None
    )
