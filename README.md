# UDM Pro MCP Server

An MCP (Model Context Protocol) server that lets Claude Code manage and monitor a Ubiquiti UDM Pro.

## Features

**46 tools** across five categories:

- **Monitoring** (12 tools) — site health, active clients, DPI stats, events, traffic reports, WAN info, system info
- **Devices** (10 tools) — list, inspect, restart, upgrade, adopt, locate, PoE power cycle, speed test
- **Clients** (6 tools) — block/unblock, disconnect, guest authorization, rename
- **Network** (12 tools) — networks/VLANs, WLANs, firewall rules, port forwarding (CRUD)
- **System** (6 tools) — reboot, backups, alarm management, DDNS status, syslog

## Setup

### 1. Install

```bash
cd ~/git/udm-pro-mcp
pip install -e .
```

### 2. Configure

Create `~/.udm-pro-mcp/config.json`:

```json
{
  "host": "192.168.1.1",
  "port": 443,
  "username": "admin",
  "password": "your-password",
  "site": "default",
  "verify_ssl": false
}
```

Override the config path with the `UDM_MCP_CONFIG` environment variable.

### 3. Add to Claude Code

```bash
claude mcp add --transport stdio udm-pro -- udm-pro-mcp
```

### 4. Verify

Run `/mcp` in Claude Code to confirm the server is connected and tools are listed.

## Usage Examples

```
"Show me the site health"
"List all my network devices"
"How many clients are connected?"
"Block client aa:bb:cc:dd:ee:ff"
"Create a new VLAN called IoT on VLAN 20 with subnet 192.168.20.1/24"
"List firewall rules"
"Run a speed test"
"Reboot the living room AP"
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Architecture

- **aiohttp** — async HTTP client with cookie jar (supports IP-based origins)
- **FastMCP** — decorator-based tool registration with lifespan context
- **Pydantic** — config validation and response summarization
- **Direct REST** — no external UniFi library; responses are summarized to 10-15 fields per object

### UDM Pro API

- Auth: `POST /api/auth/login` with cookie session + CSRF token
- Data: `GET/POST /proxy/network/api/s/{site}/{endpoint}`
- Mutations require `X-CSRF-Token` header
- Auto-reconnect on 401
