import json

from urllib.error import HTTPError, URLError

from .config import (
    GLUETUN_IP_FILE,
    HOME_PUBLIC_IP,
    IP_PROVIDERS,
    IPV4_RE,
    VPN_EXPECTED_IP,
    VPN_EXPECTED_IPS,
    VPN_ORG_KEYWORDS,
)
from .utils import fetch_json


def read_public_ip() -> dict:
    last_error = None
    resolved_ip = None
    resolved_org = None
    resolved_provider = None

    for provider in IP_PROVIDERS:
        try:
            payload = fetch_json(provider, headers={"User-Agent": "media-dashboard/1.0"})
            ip = payload.get("ip")
            org = payload.get("org") or payload.get("organization")
            if not ip:
                continue
            ip_text = str(ip).strip()
            org_text = str(org).strip() if org else None

            if resolved_ip is None:
                resolved_ip = ip_text
                resolved_provider = provider
            if org_text:
                resolved_org = org_text
                break
        except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)

    if resolved_ip:
        owner = resolved_org or lookup_ip_org(resolved_ip)
        return {
            "ip": resolved_ip,
            "org": owner,
            "provider": resolved_provider,
            "error": None,
        }

    return {"ip": None, "org": None, "provider": None, "error": last_error or "Unable to resolve public IP"}


def read_gluetun_vpn_ip() -> str | None:
    if not GLUETUN_IP_FILE.exists():
        return None
    value = GLUETUN_IP_FILE.read_text(encoding="utf-8", errors="ignore").strip()
    if not value:
        return None
    if IPV4_RE.match(value):
        return value
    return None


def lookup_ip_org(ip: str | None) -> str | None:
    if not ip:
        return None
    headers = {"User-Agent": "media-dashboard/1.0"}

    try:
        payload = fetch_json(f"https://ipinfo.io/{ip}/json", headers=headers)
        org = payload.get("org") or payload.get("organization")
        if org:
            return str(org).strip()
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
        pass

    try:
        payload = fetch_json(f"https://ipapi.co/{ip}/json/", headers=headers)
        org = payload.get("org") or payload.get("asn_org") or payload.get("asn")
        if org:
            return str(org).strip()
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
        pass

    try:
        payload = fetch_json(f"https://ipwho.is/{ip}", headers=headers)
        connection = payload.get("connection") or {}
        org = connection.get("org") or connection.get("isp") or payload.get("org")
        if org:
            return str(org).strip()
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
        pass

    return None


def vpn_status_data() -> dict:
    expected_ips = []
    if VPN_EXPECTED_IP:
        expected_ips.append(VPN_EXPECTED_IP)
    expected_ips.extend(VPN_EXPECTED_IPS)

    host_ip_result = read_public_ip()
    host_ip = host_ip_result.get("ip")
    vpn_ip = read_gluetun_vpn_ip()
    vpn_connected = bool(vpn_ip)
    current_ip = vpn_ip or host_ip
    current_org = lookup_ip_org(current_ip)
    if not current_org and current_ip and current_ip == host_ip:
        current_org = host_ip_result.get("org")
    current_org_display = current_org or ("Lookup unavailable" if current_ip else None)

    if not vpn_connected:
        status = "off"
        reason = "VPN gateway is not reporting a tunnel egress IP"
    elif not current_ip:
        status = "unknown"
        reason = host_ip_result.get("error", "Unable to resolve current public IP")
    elif expected_ips:
        status = "on" if current_ip in expected_ips else "off"
        reason = (
            "Public IP matches configured VPN endpoint"
            if status == "on"
            else "Public IP does not match configured VPN endpoint"
        )
    elif HOME_PUBLIC_IP:
        status = "off" if current_ip == HOME_PUBLIC_IP else "on"
        reason = (
            "Public IP matches HOME_PUBLIC_IP baseline (likely VPN off)"
            if status == "off"
            else "Public IP differs from HOME_PUBLIC_IP baseline (likely VPN on)"
        )
    elif VPN_ORG_KEYWORDS and current_org:
        org_lower = current_org.lower()
        matched = next((keyword for keyword in VPN_ORG_KEYWORDS if keyword in org_lower), None)
        status = "on" if matched else "off"
        reason = (
            f"IP owner matches VPN_ORG_KEYWORDS ({matched})"
            if matched
            else "IP owner does not match VPN_ORG_KEYWORDS"
        )
    else:
        status = "on"
        reason = "VPN gateway reports an active tunnel egress IP"

    return {
        "status": status,
        "reason": reason,
        "currentIp": current_ip,
        "hostIp": host_ip,
        "vpnIp": vpn_ip,
        "vpnConnected": vpn_connected,
        "currentOrg": current_org_display,
        "homeIp": HOME_PUBLIC_IP or None,
        "vpnOrgKeywords": VPN_ORG_KEYWORDS,
        "expectedIps": expected_ips,
        "provider": host_ip_result.get("provider"),
        "error": host_ip_result.get("error"),
    }
