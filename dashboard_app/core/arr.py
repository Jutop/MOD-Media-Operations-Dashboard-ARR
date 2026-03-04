import json
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

from .config import CONFIG_DIR, HTTP_TIMEOUT_SECONDS, QUEUE_LIMIT, RADARR_HOST, SABNZBD_HOST, SONARR_HOST
from .utils import (
    bool_label,
    bytes_to_human,
    collect_ready_files,
    fetch_json,
    fetch_json_optional,
    format_iso_date,
    normalize_base_path,
    normalize_records,
    parse_int,
    parse_iso_datetime,
    read_ini_value,
    read_xml_value,
    summarize_arr_queue,
    summarize_diskspace,
    summarize_health,
    summarize_rootfolders_space,
)
def arr_service_config(service_name: str) -> dict:
    if service_name == "radarr":
        config_file = CONFIG_DIR / "radarr" / "config.xml"
        api_key = read_xml_value(config_file, "ApiKey")
        url_base = normalize_base_path(read_xml_value(config_file, "UrlBase", ""))
        base_url = f"http://{RADARR_HOST}:7878{url_base}"
        return {"base_url": base_url, "api_key": api_key, "public_url": f"http://localhost:7878{url_base or '/'}"}

    if service_name == "sonarr":
        config_file = CONFIG_DIR / "sonarr" / "config.xml"
        api_key = read_xml_value(config_file, "ApiKey")
        url_base = normalize_base_path(read_xml_value(config_file, "UrlBase", ""))
        base_url = f"http://{SONARR_HOST}:8989{url_base}"
        return {"base_url": base_url, "api_key": api_key, "public_url": f"http://localhost:8989{url_base or '/'}"}

    raise ValueError(f"Unsupported ARR service: {service_name}")



def arr_rootfolders_data(service_name: str) -> dict:
    conf = arr_service_config(service_name)
    headers = {"X-Api-Key": conf["api_key"]}
    payload = fetch_json(f"{conf['base_url']}/api/v3/rootfolder", headers=headers)
    records, _ = normalize_records(payload)
    folders = [
        {
            "id": item.get("id"),
            "path": item.get("path", "-"),
            "freeSpace": bytes_to_human(item.get("freeSpace")),
            "totalSpace": bytes_to_human(item.get("totalSpace")),
            "isAccessible": bool(item.get("accessible")),
            "unmappedFolders": item.get("unmappedFolders", []),
        }
        for item in records
    ]
    return {
        "service": service_name,
        "online": True,
        "url": conf["public_url"],
        "folders": folders,
        "count": len(folders),
    }



def arr_add_rootfolder(service_name: str, path: str) -> dict:
    conf = arr_service_config(service_name)
    headers = {"X-Api-Key": conf["api_key"], "Content-Type": "application/json"}
    payload = json.dumps({"path": path}).encode("utf-8")
    request = Request(
        f"{conf['base_url']}/api/v3/rootfolder",
        data=payload,
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        response_payload = response.read().decode("utf-8")
    result = {}
    if response_payload:
        try:
            result = json.loads(response_payload)
        except json.JSONDecodeError:
            result = {}
    return {
        "ok": True,
        "service": service_name,
        "path": path,
        "result": result,
    }



def arr_delete_rootfolder(service_name: str, folder_id: int) -> dict:
    conf = arr_service_config(service_name)
    headers = {"X-Api-Key": conf["api_key"]}
    request = Request(
        f"{conf['base_url']}/api/v3/rootfolder/{int(folder_id)}",
        headers=headers,
        method="DELETE",
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        _ = response.read()
    return {
        "ok": True,
        "service": service_name,
        "folderId": int(folder_id),
    }


def _arr_request_json(conf: dict, path: str, method: str = "GET", payload: dict | None = None):
    headers = {"X-Api-Key": conf["api_key"]}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{conf['base_url']}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        response_payload = response.read().decode("utf-8")
    if not response_payload:
        return {}
    try:
        return json.loads(response_payload)
    except json.JSONDecodeError:
        return {}


def _set_download_client_field(fields: list, name: str, value):
    for field in fields:
        if field.get("name") == name:
            field["value"] = value
            return
    fields.append({"name": name, "value": value})


def configure_arr_sab_download_client(service_name: str, category: str) -> dict:
    if service_name not in {"radarr", "sonarr"}:
        return {"ok": False, "error": f"Unsupported ARR service: {service_name}"}

    conf = arr_service_config(service_name)
    sab_config_file = CONFIG_DIR / "sabnzbd" / "sabnzbd.ini"
    sab_api_key = read_ini_value(sab_config_file, "api_key")
    sab_url_base = normalize_base_path(read_ini_value(sab_config_file, "url_base"))
    sab_username = read_ini_value(sab_config_file, "username")
    sab_password = read_ini_value(sab_config_file, "password")
    if not sab_api_key:
        return {"ok": False, "error": "SABnzbd API key not found in config"}

    clients = _arr_request_json(conf, "/api/v3/downloadclient")
    if not isinstance(clients, list):
        clients = []
    existing = next(
        (
            item
            for item in clients
            if str(item.get("implementation", "")).lower() == "sabnzbd"
            or str(item.get("implementationName", "")).lower() == "sabnzbd"
        ),
        None,
    )

    payload = {}
    mode = "create"
    endpoint = "/api/v3/downloadclient"
    method = "POST"
    if existing:
        payload = existing
        mode = "update"
        client_id = existing.get("id")
        endpoint = f"/api/v3/downloadclient/{client_id}"
        method = "PUT"
    else:
        schema = _arr_request_json(conf, "/api/v3/downloadclient/schema")
        if not isinstance(schema, list):
            schema = []
        template = next((item for item in schema if item.get("implementation") == "Sabnzbd"), None)
        if not template:
            return {"ok": False, "error": "Could not find Sabnzbd schema in ARR"}
        payload = {
            "enable": bool(template.get("enable", True)),
            "protocol": template.get("protocol", "usenet"),
            "priority": int(template.get("priority", 1)),
            "removeCompletedDownloads": bool(template.get("removeCompletedDownloads", True)),
            "removeFailedDownloads": bool(template.get("removeFailedDownloads", True)),
            "name": template.get("name") or "SABnzbd",
            "fields": template.get("fields", []),
            "implementationName": template.get("implementationName", "SABnzbd"),
            "implementation": template.get("implementation", "Sabnzbd"),
            "configContract": template.get("configContract", "SabnzbdSettings"),
            "tags": template.get("tags", []),
        }

    payload["enable"] = True
    payload["priority"] = 1
    payload["removeCompletedDownloads"] = True
    payload["removeFailedDownloads"] = True
    payload["name"] = "SABnzbd"
    payload["implementation"] = "Sabnzbd"
    payload["implementationName"] = "SABnzbd"
    payload["configContract"] = payload.get("configContract") or "SabnzbdSettings"
    payload["fields"] = list(payload.get("fields") or [])

    _set_download_client_field(payload["fields"], "host", SABNZBD_HOST or "localhost")
    _set_download_client_field(payload["fields"], "port", 8080)
    _set_download_client_field(payload["fields"], "useSsl", False)
    _set_download_client_field(payload["fields"], "urlBase", sab_url_base)
    _set_download_client_field(payload["fields"], "apiKey", sab_api_key)
    _set_download_client_field(payload["fields"], "username", sab_username)
    _set_download_client_field(payload["fields"], "password", sab_password)

    if service_name == "radarr":
        _set_download_client_field(payload["fields"], "movieCategory", category or "movies")
        _set_download_client_field(payload["fields"], "recentMoviePriority", -100)
        _set_download_client_field(payload["fields"], "olderMoviePriority", -100)
    else:
        _set_download_client_field(payload["fields"], "tvCategory", category or "tv")
        _set_download_client_field(payload["fields"], "recentTvPriority", -100)
        _set_download_client_field(payload["fields"], "olderTvPriority", -100)

    response = _arr_request_json(conf, endpoint, method=method, payload=payload)
    return {
        "ok": True,
        "service": service_name,
        "mode": mode,
        "endpoint": endpoint,
        "result": response,
    }




def radarr_data() -> dict:
    config_file = CONFIG_DIR / "radarr" / "config.xml"
    api_key = read_xml_value(config_file, "ApiKey")
    url_base = normalize_base_path(read_xml_value(config_file, "UrlBase", ""))
    base_url = f"http://{RADARR_HOST}:7878{url_base}"
    headers = {"X-Api-Key": api_key}

    system = fetch_json(f"{base_url}/api/v3/system/status", headers=headers)
    queue = fetch_json(f"{base_url}/api/v3/queue/details?page=1&pageSize={QUEUE_LIMIT}", headers=headers)
    queue_records, queue_total = normalize_records(queue)
    movies = fetch_json(f"{base_url}/api/v3/movie", headers=headers)
    movie_records, movie_total = normalize_records(movies)
    wanted_payload = fetch_json_optional(
        f"{base_url}/api/v3/wanted/missing?page=1&pageSize=1",
        headers=headers,
        default={"records": [], "totalRecords": 0},
    )
    _, wanted_total = normalize_records(wanted_payload)
    health_payload = fetch_json_optional(f"{base_url}/api/v3/health", headers=headers, default=[])
    disk_payload = fetch_json_optional(f"{base_url}/api/v3/diskspace", headers=headers, default=[])
    rootfolders_payload = fetch_json_optional(f"{base_url}/api/v3/rootfolder", headers=headers, default=[])
    ready_records = collect_ready_files(("movies", "movie", "films"))
    queue_items, queue_summary = summarize_arr_queue(queue_records)

    today_date = datetime.now(timezone.utc).date()
    today = today_date.isoformat()
    end = (today_date + timedelta(days=45)).isoformat()

    calendar = fetch_json(
        f"{base_url}/api/v3/calendar?start={today}&end={end}&includeMovie=true",
        headers=headers,
    )
    calendar_records, _ = normalize_records(calendar)
    future_records = []
    for item in calendar_records:
        release_value = (
            item.get("digitalRelease")
            or item.get("physicalRelease")
            or item.get("inCinemas")
            or item.get("releaseDate")
        )
        release_dt = parse_iso_datetime(release_value)
        if release_dt == datetime.min.replace(tzinfo=timezone.utc):
            continue
        if release_dt.date().isoformat() < today:
            continue
        future_records.append((release_dt, item))
    future_records.sort(key=lambda pair: pair[0])

    monitored = sum(1 for movie in movie_records if movie.get("monitored"))
    downloaded = sum(1 for movie in movie_records if movie.get("hasFile"))
    missing = sum(1 for movie in movie_records if movie.get("monitored") and not movie.get("hasFile"))
    total_size_on_disk = sum(parse_int(movie.get("sizeOnDisk")) or 0 for movie in movie_records)
    upcoming_7_days = sum(1 for dt, _ in future_records if (dt.date() - today_date).days <= 7)
    upcoming_30_days = sum(1 for dt, _ in future_records if (dt.date() - today_date).days <= 30)
    health_summary = summarize_health(health_payload)
    rootfolder_disk_summary = summarize_rootfolders_space(rootfolders_payload)
    disk_summary = rootfolder_disk_summary if rootfolder_disk_summary.get("volumeCount", 0) > 0 else summarize_diskspace(disk_payload)

    return {
        "online": True,
        "url": f"http://localhost:7878{url_base or '/'}",
        "system": {
            "version": system.get("version", "unknown"),
            "appName": system.get("appName", "Radarr"),
            "instanceName": system.get("instanceName", "Radarr"),
            "osName": system.get("osName", "-"),
            "isDebug": bool(system.get("isDebug")),
        },
        "stats": {
            "libraryTotal": movie_total,
            "monitored": monitored,
            "downloaded": downloaded,
            "missing": missing,
            "wanted": wanted_total,
            "unmonitored": max(0, movie_total - monitored),
            "sizeOnDisk": total_size_on_disk,
            "sizeOnDiskReadable": bytes_to_human(total_size_on_disk),
            "upcoming7Days": upcoming_7_days,
            "upcoming30Days": upcoming_30_days,
        },
        "queueSummary": queue_summary,
        "health": health_summary,
        "disk": disk_summary,
        "readyCount": len(ready_records),
        "ready": ready_records,
        "upcomingCount": len(future_records),
        "upcoming": [
            {
                "title": f"{item.get('title', 'Unknown')} ({item.get('year', '-')})",
                "date": format_iso_date(
                    item.get("digitalRelease")
                    or item.get("physicalRelease")
                    or item.get("inCinemas")
                    or item.get("releaseDate")
                ),
                "status": item.get("status", "-"),
                "availability": item.get("minimumAvailability", "-"),
            }
            for _, item in future_records[:QUEUE_LIMIT]
        ],
        "queueCount": queue_total,
        "queue": queue_items,
        "libraryCount": movie_total,
    }



def sonarr_data() -> dict:
    config_file = CONFIG_DIR / "sonarr" / "config.xml"
    api_key = read_xml_value(config_file, "ApiKey")
    url_base = normalize_base_path(read_xml_value(config_file, "UrlBase", ""))
    base_url = f"http://{SONARR_HOST}:8989{url_base}"
    headers = {"X-Api-Key": api_key}

    system = fetch_json(f"{base_url}/api/v3/system/status", headers=headers)
    queue = fetch_json(f"{base_url}/api/v3/queue/details?page=1&pageSize={QUEUE_LIMIT}", headers=headers)
    queue_records, queue_total = normalize_records(queue)
    series = fetch_json(f"{base_url}/api/v3/series", headers=headers)
    series_records, series_total = normalize_records(series)
    wanted_payload = fetch_json_optional(
        f"{base_url}/api/v3/wanted/missing?page=1&pageSize=1",
        headers=headers,
        default={"records": [], "totalRecords": 0},
    )
    _, wanted_total = normalize_records(wanted_payload)
    health_payload = fetch_json_optional(f"{base_url}/api/v3/health", headers=headers, default=[])
    disk_payload = fetch_json_optional(f"{base_url}/api/v3/diskspace", headers=headers, default=[])
    rootfolders_payload = fetch_json_optional(f"{base_url}/api/v3/rootfolder", headers=headers, default=[])
    ready_records = collect_ready_files(("tv", "shows", "series"))
    queue_items, queue_summary = summarize_arr_queue(queue_records)

    today_date = datetime.now(timezone.utc).date()
    today = today_date.isoformat()
    end = (today_date + timedelta(days=45)).isoformat()

    calendar = fetch_json(
        f"{base_url}/api/v3/calendar?start={today}&end={end}&includeSeries=true",
        headers=headers,
    )
    calendar_records, _ = normalize_records(calendar)
    future_records = []
    for item in calendar_records:
        air_dt = parse_iso_datetime(item.get("airDateUtc") or item.get("airDate"))
        if air_dt == datetime.min.replace(tzinfo=timezone.utc):
            continue
        if air_dt.date().isoformat() < today:
            continue
        future_records.append((air_dt, item))
    future_records.sort(key=lambda pair: pair[0])

    monitored = sum(1 for item in series_records if item.get("monitored"))
    continuing = sum(1 for item in series_records if str(item.get("status", "")).lower() == "continuing")
    ended = sum(1 for item in series_records if str(item.get("status", "")).lower() == "ended")
    total_episode_count = 0
    episode_file_count = 0
    total_size_on_disk = 0
    for item in series_records:
        stats = item.get("statistics") or {}
        total_episode_count += parse_int(stats.get("episodeCount") or stats.get("totalEpisodeCount")) or 0
        episode_file_count += parse_int(stats.get("episodeFileCount")) or 0
        total_size_on_disk += parse_int(stats.get("sizeOnDisk")) or 0

    missing_episodes = max(0, total_episode_count - episode_file_count)
    upcoming_7_days = sum(1 for dt, _ in future_records if (dt.date() - today_date).days <= 7)
    upcoming_30_days = sum(1 for dt, _ in future_records if (dt.date() - today_date).days <= 30)
    health_summary = summarize_health(health_payload)
    rootfolder_disk_summary = summarize_rootfolders_space(rootfolders_payload)
    disk_summary = rootfolder_disk_summary if rootfolder_disk_summary.get("volumeCount", 0) > 0 else summarize_diskspace(disk_payload)

    return {
        "online": True,
        "url": f"http://localhost:8989{url_base or '/'}",
        "system": {
            "version": system.get("version", "unknown"),
            "appName": system.get("appName", "Sonarr"),
            "instanceName": system.get("instanceName", "Sonarr"),
            "osName": system.get("osName", "-"),
            "isDebug": bool(system.get("isDebug")),
        },
        "stats": {
            "libraryTotal": series_total,
            "monitored": monitored,
            "unmonitored": max(0, series_total - monitored),
            "continuing": continuing,
            "ended": ended,
            "totalEpisodes": total_episode_count,
            "episodeFiles": episode_file_count,
            "missingEpisodes": missing_episodes,
            "wanted": wanted_total,
            "sizeOnDisk": total_size_on_disk,
            "sizeOnDiskReadable": bytes_to_human(total_size_on_disk),
            "upcoming7Days": upcoming_7_days,
            "upcoming30Days": upcoming_30_days,
        },
        "queueSummary": queue_summary,
        "health": health_summary,
        "disk": disk_summary,
        "readyCount": len(ready_records),
        "ready": ready_records,
        "upcomingCount": len(future_records),
        "upcoming": [
            {
                "title": item.get("series", {}).get("title", "Unknown Series"),
                "date": format_iso_date(item.get("airDateUtc") or item.get("airDate")),
                "episode": f"S{int(item.get('seasonNumber', 0)):02d}E{int(item.get('episodeNumber', 0)):02d} - {item.get('title', '-')}",
                "monitored": bool_label(item.get("monitored")),
            }
            for _, item in future_records[:QUEUE_LIMIT]
        ],
        "queueCount": queue_total,
        "queue": queue_items,
        "libraryCount": series_total,
    }




