"""Tests for config loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from udm_pro_mcp.config import load_config
from udm_pro_mcp.errors import ConfigError


def test_load_config_valid(tmp_path, monkeypatch):
    cfg = {
        "host": "10.0.0.1",
        "port": 443,
        "username": "admin",
        "password": "secret",
        "site": "default",
        "verify_ssl": False,
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg))
    monkeypatch.setenv("UDM_MCP_CONFIG", str(path))

    config = load_config()
    assert config.host == "10.0.0.1"
    assert config.password == "secret"
    assert config.base_url == "https://10.0.0.1:443"


def test_load_config_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("UDM_MCP_CONFIG", str(tmp_path / "nope.json"))
    with pytest.raises(ConfigError, match="not found"):
        load_config()


def test_load_config_invalid_json(tmp_path, monkeypatch):
    path = tmp_path / "bad.json"
    path.write_text("{invalid")
    monkeypatch.setenv("UDM_MCP_CONFIG", str(path))
    with pytest.raises(ConfigError, match="Invalid JSON"):
        load_config()


def test_load_config_missing_password(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"host": "10.0.0.1"}))
    monkeypatch.setenv("UDM_MCP_CONFIG", str(path))
    with pytest.raises(ConfigError, match="Invalid config"):
        load_config()


def test_config_defaults(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"password": "pw"}))
    monkeypatch.setenv("UDM_MCP_CONFIG", str(path))
    config = load_config()
    assert config.host == "192.168.1.1"
    assert config.port == 443
    assert config.site == "default"
    assert config.verify_ssl is False
