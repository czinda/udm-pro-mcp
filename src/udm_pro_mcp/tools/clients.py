"""Client management tools: block, unblock, disconnect, guest auth."""

from __future__ import annotations

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ..server import AppContext, mcp


def _client(ctx: Context[ServerSession, AppContext]):
    return ctx.request_context.lifespan_context.client


@mcp.tool()
async def block_client(mac: str, ctx: Context[ServerSession, AppContext]) -> str:
    """Block a client by MAC address, preventing it from accessing the network."""
    mac = mac.lower().replace("-", ":")
    await _client(ctx).post_cmd("stamgr", "block-sta", mac=mac)
    return f"Client {mac} has been blocked."


@mcp.tool()
async def unblock_client(mac: str, ctx: Context[ServerSession, AppContext]) -> str:
    """Unblock a previously blocked client by MAC address."""
    mac = mac.lower().replace("-", ":")
    await _client(ctx).post_cmd("stamgr", "unblock-sta", mac=mac)
    return f"Client {mac} has been unblocked."


@mcp.tool()
async def disconnect_client(mac: str, ctx: Context[ServerSession, AppContext]) -> str:
    """Force-disconnect a client. It may reconnect automatically."""
    mac = mac.lower().replace("-", ":")
    await _client(ctx).post_cmd("stamgr", "kick-sta", mac=mac)
    return f"Client {mac} has been disconnected."


@mcp.tool()
async def authorize_guest(
    mac: str,
    minutes: int = 60,
    up_kbps: int | None = None,
    down_kbps: int | None = None,
    quota_mb: int | None = None,
    ctx: Context[ServerSession, AppContext] = None,  # type: ignore[assignment]
) -> str:
    """Authorize a guest client for network access.

    Args:
        mac: Client MAC address.
        minutes: Duration of authorization in minutes.
        up_kbps: Upload speed limit in Kbps (optional).
        down_kbps: Download speed limit in Kbps (optional).
        quota_mb: Data quota in MB (optional).
    """
    mac = mac.lower().replace("-", ":")
    kwargs: dict = {"mac": mac, "minutes": minutes}
    if up_kbps is not None:
        kwargs["up"] = up_kbps
    if down_kbps is not None:
        kwargs["down"] = down_kbps
    if quota_mb is not None:
        kwargs["bytes"] = quota_mb
    await _client(ctx).post_cmd("stamgr", "authorize-guest", **kwargs)
    return f"Guest {mac} authorized for {minutes} minutes."


@mcp.tool()
async def unauthorize_guest(
    mac: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Revoke guest authorization for a client."""
    mac = mac.lower().replace("-", ":")
    await _client(ctx).post_cmd("stamgr", "unauthorize-guest", mac=mac)
    return f"Guest authorization revoked for {mac}."


@mcp.tool()
async def set_client_name(
    mac: str, name: str, ctx: Context[ServerSession, AppContext]
) -> str:
    """Set a friendly name for a client (alias)."""
    mac = mac.lower().replace("-", ":")
    # First get the user ID
    data = await _client(ctx).get(f"stat/user/{mac}")
    if not data:
        return f"Client {mac} not found."
    user_id = data[0].get("_id")
    await _client(ctx).put(f"rest/user/{user_id}", {"name": name})
    return f"Client {mac} name set to '{name}'."
