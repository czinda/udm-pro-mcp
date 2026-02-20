"""FastMCP server entry point for UDM Pro management."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from .client import UDMProClient
from .config import load_config

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Typed application context holding the API client."""

    client: UDMProClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize the UDM Pro client on startup, close on shutdown."""
    config = load_config()
    client = UDMProClient(config)
    await client.connect()
    logger.info("UDM Pro MCP server connected to %s", config.host)
    try:
        yield AppContext(client=client)
    finally:
        await client.close()
        logger.info("UDM Pro MCP server disconnected")


mcp = FastMCP(
    "UDM Pro",
    instructions="Manage and monitor a Ubiquiti UDM Pro",
    lifespan=app_lifespan,
)

# Import tool modules so their @mcp.tool() decorators register with the server.
# This must happen after `mcp` is defined.
from .tools import clients as _clients  # noqa: F401, E402
from .tools import devices as _devices  # noqa: F401, E402
from .tools import monitoring as _monitoring  # noqa: F401, E402
from .tools import network as _network  # noqa: F401, E402
from .tools import system as _system  # noqa: F401, E402


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    main()
