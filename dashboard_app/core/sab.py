import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import CONFIG_DIR, HTTP_TIMEOUT_SECONDS, QUEUE_LIMIT, SABNZBD_HOST
from .utils import (
    bytes_to_gb,
    calculate_progress,
    fetch_json,
    fetch_json_optional,
    format_iso_date,
    normalize_base_path,
    parse_float,
    parse_int,
    read_ini_value,
)
def sab_service_config() -> dict:
    config_file = CONFIG_DIR / "sabnzbd" / "sabnzbd.ini"
    api_key = read_ini_value(config_file, "api_key")
    url_base = normalize_base_path(read_ini_value(config_file, "url_base"))
    base_url = f"http://{SABNZBD_HOST}:8080{url_base}"
    return {"base_url": base_url, "api_key": api_key, "public_url": f"http://localhost:8080{url_base or '/'}"}



def sab_get_config_value(keyword: str) -> str | None:
    conf = sab_service_config()
    query = urlencode(
        {
            "mode": "get_config",
            "section": "misc",
            "keyword": keyword,
            "output": "json",
            "apikey": conf["api_key"],
        }
    )
    payload = fetch_json(f"{conf['base_url']}/api?{query}")
    value = payload.get("config", {}).get("misc", {}).get(keyword)
    if value is None:
        value = payload.get("value")
    if value is None:
        return None
    return str(value)



def sab_set_config_value(keyword: str, value: str) -> dict:
    conf = sab_service_config()
    query = urlencode(
        {
            "mode": "set_config",
            "section": "misc",
            "keyword": keyword,
            "value": value,
            "output": "json",
            "apikey": conf["api_key"],
        }
    )
    payload = fetch_json(f"{conf['base_url']}/api?{query}")
    status = payload.get("status", payload.get("result", payload.get("success")))
    return {
        "ok": bool(status in (True, "ok", "OK", "true", "True", 1, "1")),
        "raw": payload,
        "keyword": keyword,
        "value": value,
    }



def sab_paths_data() -> dict:
    conf = sab_service_config()
    complete_dir = sab_get_config_value("complete_dir")
    incomplete_dir = sab_get_config_value("download_dir")
    script_dir = sab_get_config_value("script_dir")
    return {
        "online": True,
        "url": conf["public_url"],
        "paths": {
            "completeDir": complete_dir or "-",
            "downloadDir": incomplete_dir or "-",
            "scriptDir": script_dir or "-",
        },
    }



def set_sab_paths(download_dir: str | None, complete_dir: str | None) -> dict:
    updates = []
    if download_dir is not None:
        updates.append(sab_set_config_value("download_dir", download_dir))
    if complete_dir is not None:
        updates.append(sab_set_config_value("complete_dir", complete_dir))
    return {
        "ok": all(item.get("ok") for item in updates) if updates else False,
        "updates": updates,
    }




def sabnzbd_data() -> dict:
    config_file = CONFIG_DIR / "sabnzbd" / "sabnzbd.ini"
    api_key = read_ini_value(config_file, "api_key")
    url_base = normalize_base_path(read_ini_value(config_file, "url_base"))
    base_url = f"http://{SABNZBD_HOST}:8080{url_base}"

    queue_query = urlencode(
        {
            "mode": "queue",
            "output": "json",
            "limit": str(QUEUE_LIMIT),
            "apikey": api_key,
        }
    )
    history_query = urlencode(
        {
            "mode": "history",
            "output": "json",
            "limit": str(QUEUE_LIMIT),
            "apikey": api_key,
        }
    )
    history_archive_query = urlencode(
        {
            "mode": "history",
            "output": "json",
            "limit": str(QUEUE_LIMIT),
            "archive": "1",
            "apikey": api_key,
        }
    )
    server_stats_query = urlencode(
        {
            "mode": "server_stats",
            "output": "json",
            "apikey": api_key,
        }
    )

    queue_payload = fetch_json(f"{base_url}/api?{queue_query}")
    history_payload = fetch_json(f"{base_url}/api?{history_query}")
    archive_history_payload = fetch_json(f"{base_url}/api?{history_archive_query}")
    server_stats_payload = fetch_json_optional(f"{base_url}/api?{server_stats_query}", default={}) or {}

    queue_data = queue_payload.get("queue", {})
    slots = queue_data.get("slots", [])
    history_slots = history_payload.get("history", {}).get("slots", []) or []
    archive_history_slots = archive_history_payload.get("history", {}).get("slots", []) or []
    if not history_slots and archive_history_slots:
        history_slots = archive_history_slots

    queue_items = []
    for item in slots[:QUEUE_LIMIT]:
        size_mb = parse_float(item.get("mb"))
        size_left_mb = parse_float(item.get("mbleft"))
        queue_items.append(
            {
                "id": item.get("nzo_id"),
                "title": item.get("filename", "Unknown"),
                "status": item.get("status", "-"),
                "category": item.get("cat", "-"),
                "priority": item.get("priority", "-"),
                "size": f"{item.get('mb', '-') } MB",
                "sizeLeft": f"{item.get('mbleft', '-') } MB",
                "sizeMb": size_mb,
                "sizeLeftMb": size_left_mb,
                "progressPercent": calculate_progress(size_mb, size_left_mb),
                "timeLeft": item.get("timeleft", "-"),
                "downloadClient": "SABnzbd",
            }
        )

    history_items = [
        {
            "title": item.get("name", "Unknown"),
            "status": item.get("status", "-"),
            "category": item.get("category", "-"),
            "size": bytes_to_gb(item.get("bytes")),
            "completed": format_iso_date(item.get("completed")),
        }
        for item in history_slots[:QUEUE_LIMIT]
    ]

    queue_total_mb = sum((item.get("sizeMb") or 0) for item in queue_items)
    queue_left_mb = sum((item.get("sizeLeftMb") or 0) for item in queue_items)
    completed_count = sum(1 for item in history_slots if str(item.get("status", "")).lower() == "completed")
    failed_count = sum(1 for item in history_slots if str(item.get("status", "")).lower() in {"failed", "repair_failed"})

    stats_block = server_stats_payload.get("server_stats", {}) if isinstance(server_stats_payload, dict) else {}
    transfer_stats = {
        "day": stats_block.get("day_size") or stats_block.get("day", "-"),
        "week": stats_block.get("week_size") or stats_block.get("week", "-"),
        "month": stats_block.get("month_size") or stats_block.get("month", "-"),
        "total": stats_block.get("total_size") or stats_block.get("total", "-"),
    }

    return {
        "online": True,
        "url": f"http://localhost:8080{url_base or '/'}",
        "system": {
            "version": queue_data.get("version", "unknown"),
            "status": queue_data.get("status", "-"),
            "paused": bool(queue_data.get("paused", False)),
            "speed": queue_data.get("speed", "-"),
            "size": queue_data.get("size", "-"),
            "sizeLeft": queue_data.get("mbleft", "-"),
            "eta": queue_data.get("timeleft", "-"),
        },
        "stats": {
            "queueItems": int(queue_data.get("noofslots_total") or len(slots)),
            "queueTotalMb": round(queue_total_mb, 2),
            "queueLeftMb": round(queue_left_mb, 2),
            "completedJobs": completed_count,
            "failedJobs": failed_count,
            "paused": bool(queue_data.get("paused", False)),
            "historyItems": len(history_slots),
        },
        "transferStats": transfer_stats,
        "queueCount": int(queue_data.get("noofslots_total") or len(slots)),
        "queue": queue_items,
        "history": history_items,
        "libraryCount": 0,
        "library": [],
    }




