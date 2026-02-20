"""Tests for system tools."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_archive_all_alarms(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.system import archive_all_alarms
    result = await archive_all_alarms(mock_ctx)
    assert "archived" in result


@pytest.mark.asyncio
async def test_create_backup(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.system import create_backup
    result = await create_backup(mock_ctx)
    assert "Backup initiated" in result


@pytest.mark.asyncio
async def test_list_backups(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = [
        {"filename": "backup_2024.unf", "size": 12345, "datetime": "2024-01-15"}
    ]
    from udm_pro_mcp.tools.system import list_backups
    result = await list_backups(mock_ctx)
    assert "backup_2024.unf" in result


@pytest.mark.asyncio
async def test_list_backups_empty(mock_ctx, mock_api_client):
    mock_api_client.post_cmd.return_value = []
    from udm_pro_mcp.tools.system import list_backups
    result = await list_backups(mock_ctx)
    assert result == "No backups found."


@pytest.mark.asyncio
async def test_reboot_udm(mock_ctx, mock_api_client):
    mock_api_client.get.return_value = [
        {"mac": "aa:bb:cc:00:00:01", "type": "udm", "name": "UDM Pro"}
    ]
    mock_api_client.post_cmd.return_value = {}
    from udm_pro_mcp.tools.system import reboot_udm
    result = await reboot_udm(mock_ctx)
    assert "Reboot command sent" in result
