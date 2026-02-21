"""Pydantic models for configuration and response summaries."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UDMConfig(BaseModel):
    """UDM Pro connection configuration."""

    host: str = "192.168.1.1"
    port: int = 443
    username: str = "admin"
    password: str
    site: str = "default"
    verify_ssl: bool = False

    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.port}"


# --- Response summary models ---
# These extract the most useful fields from verbose API responses.


class DeviceSummary(BaseModel):
    mac: str = ""
    name: str = ""
    model: str = ""
    type: str = ""
    ip: str = ""
    version: str = ""
    adopted: bool = False
    state: int = 0
    uptime: int = 0
    num_sta: int = Field(0, description="Number of connected stations")
    tx_bytes: int = 0
    rx_bytes: int = 0
    upgradable: bool = False
    upgrade_to_firmware: str = ""

    @classmethod
    def from_api(cls, data: dict) -> DeviceSummary:
        return cls(
            mac=data.get("mac", ""),
            name=data.get("name", data.get("hostname", "")),
            model=data.get("model", ""),
            type=data.get("type", ""),
            ip=data.get("ip", data.get("connect_request_ip", "")),
            version=data.get("version", ""),
            adopted=data.get("adopted", False),
            state=data.get("state", 0),
            uptime=data.get("uptime", 0),
            num_sta=data.get("num_sta", 0),
            tx_bytes=data.get("tx_bytes", 0),
            rx_bytes=data.get("rx_bytes", 0),
            upgradable=data.get("upgradable", False),
            upgrade_to_firmware=data.get("upgrade_to_firmware", ""),
        )


class ClientSummary(BaseModel):
    mac: str = ""
    hostname: str = ""
    ip: str = ""
    network: str = ""
    oui: str = ""
    is_wired: bool = False
    is_guest: bool = False
    tx_bytes: int = 0
    rx_bytes: int = 0
    uptime: int = 0
    signal: int | None = None
    satisfaction: int | None = None
    sw_port: int | None = None

    @classmethod
    def from_api(cls, data: dict) -> ClientSummary:
        return cls(
            mac=data.get("mac", ""),
            hostname=data.get("hostname", data.get("name", "")),
            ip=data.get("ip", ""),
            network=data.get("network", data.get("network_id", "")),
            oui=data.get("oui", ""),
            is_wired=data.get("is_wired", False),
            is_guest=data.get("is_guest", False),
            tx_bytes=data.get("tx_bytes", 0),
            rx_bytes=data.get("rx_bytes", 0),
            uptime=data.get("uptime", 0),
            signal=data.get("signal"),
            satisfaction=data.get("satisfaction"),
            sw_port=data.get("sw_port"),
        )


class NetworkSummary(BaseModel):
    id: str = ""
    name: str = ""
    purpose: str = ""
    vlan: int | None = None
    subnet: str = ""
    dhcp_enabled: bool = False
    domain_name: str = ""
    enabled: bool = True

    @classmethod
    def from_api(cls, data: dict) -> NetworkSummary:
        return cls(
            id=data.get("_id", ""),
            name=data.get("name", ""),
            purpose=data.get("purpose", ""),
            vlan=data.get("vlan"),
            subnet=data.get("ip_subnet", ""),
            dhcp_enabled=data.get("dhcpd_enabled", False),
            domain_name=data.get("domain_name", ""),
            enabled=data.get("enabled", True),
        )


class WLANSummary(BaseModel):
    id: str = ""
    name: str = ""
    enabled: bool = True
    security: str = ""
    wpa_mode: str = ""
    is_guest: bool = False
    network_id: str = ""
    hide_ssid: bool = False

    @classmethod
    def from_api(cls, data: dict) -> WLANSummary:
        return cls(
            id=data.get("_id", ""),
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            security=data.get("security", ""),
            wpa_mode=data.get("wpa_mode", ""),
            is_guest=data.get("is_guest", False),
            network_id=data.get("networkconf_id", ""),
            hide_ssid=data.get("hide_ssid", False),
        )


class FirewallRuleSummary(BaseModel):
    id: str = ""
    name: str = ""
    ruleset: str = ""
    rule_index: int = 0
    action: str = ""
    enabled: bool = True
    protocol: str = ""
    src_network_id: str = ""
    dst_network_id: str = ""

    @classmethod
    def from_api(cls, data: dict) -> FirewallRuleSummary:
        return cls(
            id=data.get("_id", ""),
            name=data.get("name", ""),
            ruleset=data.get("ruleset", ""),
            rule_index=data.get("rule_index", 0),
            action=data.get("action", ""),
            enabled=data.get("enabled", True),
            protocol=data.get("protocol", ""),
            src_network_id=data.get("src_networkconf_id", ""),
            dst_network_id=data.get("dst_networkconf_id", ""),
        )


class PortForwardSummary(BaseModel):
    id: str = ""
    name: str = ""
    enabled: bool = True
    src: str = ""
    dst_port: str = ""
    fwd: str = ""
    fwd_port: str = ""
    proto: str = ""

    @classmethod
    def from_api(cls, data: dict) -> PortForwardSummary:
        return cls(
            id=data.get("_id", ""),
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            src=data.get("src", "any"),
            dst_port=data.get("dst_port", ""),
            fwd=data.get("fwd", ""),
            fwd_port=data.get("fwd_port", ""),
            proto=data.get("proto", "tcp_udp"),
        )


class EventSummary(BaseModel):
    key: str = ""
    msg: str = ""
    time: int = 0
    subsystem: str = ""
    site_id: str = ""

    @classmethod
    def from_api(cls, data: dict) -> EventSummary:
        return cls(
            key=data.get("key", ""),
            msg=data.get("msg", ""),
            time=data.get("time", 0),
            subsystem=data.get("subsystem", ""),
            site_id=data.get("site_id", ""),
        )


class AlarmSummary(BaseModel):
    id: str = ""
    key: str = ""
    msg: str = ""
    time: int = 0
    archived: bool = False

    @classmethod
    def from_api(cls, data: dict) -> AlarmSummary:
        return cls(
            id=data.get("_id", ""),
            key=data.get("key", ""),
            msg=data.get("msg", ""),
            time=data.get("time", 0),
            archived=data.get("archived", False),
        )
