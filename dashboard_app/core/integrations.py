import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

from .arr import radarr_data, sonarr_data
from .containers import container_states, perform_container_action
from .network import vpn_status_data
from .ombi import ombi_data
from .sab import sab_paths_data, sabnzbd_data, set_sab_paths


def service_result_light(fetcher):
    try:
        payload = fetcher()
        payload["error"] = None
        return payload
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {
            "online": False,
            "error": str(exc),
        }


def service_result(fetcher):
    try:
        data = fetcher()
        data["error"] = None
        return data
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {
            "online": False,
            "error": str(exc),
            "url": "#",
            "system": {},
            "stats": {},
            "queueSummary": {},
            "health": {"totalIssues": 0, "warnings": 0, "errors": 0, "items": []},
            "disk": {"totalSpace": 0, "freeSpace": 0, "totalReadable": "-", "freeReadable": "-", "usedPercent": None, "volumes": []},
            "readyCount": 0,
            "ready": [],
            "upcomingCount": 0,
            "upcoming": [],
            "queueCount": 0,
            "queue": [],
            "history": [],
            "libraryCount": 0,
            "library": [],
        }


def build_overview_summary(services: dict, network: dict) -> dict:
    online_services = sum(1 for service in services.values() if service.get("online"))
    total_services = len(services)
    queue_total = sum(int(service.get("queueCount") or 0) for service in services.values())
    ready_total = sum(int(service.get("readyCount") or 0) for service in services.values())
    upcoming_total = sum(int(service.get("upcomingCount") or 0) for service in services.values())
    library_total = sum(int(service.get("libraryCount") or 0) for service in services.values())
    issue_total = sum(int((service.get("health") or {}).get("totalIssues") or 0) for service in services.values())
    return {
        "onlineServices": online_services,
        "totalServices": total_services,
        "queueTotal": queue_total,
        "readyTotal": ready_total,
        "upcomingTotal": upcoming_total,
        "libraryTotal": library_total,
        "serviceIssues": issue_total,
        "vpnStatus": network.get("status", "unknown"),
    }


def build_dashboard_payload() -> dict:
    network = vpn_status_data()
    services = {
        "radarr": service_result(radarr_data),
        "sonarr": service_result(sonarr_data),
        "sabnzbd": service_result(sabnzbd_data),
        "ombi": service_result(ombi_data),
    }
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "network": network,
        "services": services,
        "summary": build_overview_summary(services, network),
    }


def build_sab_payload() -> dict:
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sabnzbd": service_result(sabnzbd_data),
    }


def build_admin_payload() -> dict:
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "containers": container_states(),
        "settings": {
            "sabnzbd": service_result_light(sab_paths_data),
        },
    }
