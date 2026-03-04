import json
import sqlite3
from urllib.request import Request, urlopen

from .config import CONFIG_DIR, HTTP_TIMEOUT_SECONDS, OMBI_HOST, OMBI_URL_BASE
from .utils import fetch_json, fetch_json_optional, normalize_base_path, parse_int, read_xml_value


def _ombi_base_url() -> str:
    url_base = normalize_base_path(OMBI_URL_BASE)
    return f"http://{OMBI_HOST}:3579{url_base}"


def _ombi_api_key_from_settings_db() -> str:
    db_file = CONFIG_DIR / "ombi" / "OmbiSettings.db"
    if not db_file.exists():
        return ""
    try:
        con = sqlite3.connect(str(db_file))
        cur = con.cursor()
        row = cur.execute(
            "SELECT Content FROM GlobalSettings WHERE SettingsName='OmbiSettings' LIMIT 1"
        ).fetchone()
        con.close()
        if not row or not row[0]:
            return ""
        payload = json.loads(row[0])
        return str(payload.get("ApiKey") or "").strip()
    except (OSError, ValueError, sqlite3.DatabaseError, json.JSONDecodeError):
        return ""


def _ombi_request(path: str, api_key: str, method: str = "GET", payload: dict | None = None):
    headers = {"ApiKey": api_key}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    request = Request(f"{_ombi_base_url()}{path}", data=body, headers=headers, method=method)
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        response_payload = response.read().decode("utf-8")
    if not response_payload:
        return {}
    try:
        return json.loads(response_payload)
    except json.JSONDecodeError:
        return {"raw": response_payload}


def configure_ombi_arr_integrations(
    radarr_api_key: str,
    sonarr_api_key: str,
    radarr_root_path: str,
) -> dict:
    ombi_api_key = _ombi_api_key_from_settings_db()
    if not ombi_api_key:
        return {"ok": False, "error": "Ombi API key not found in settings database"}

    radarr_url_base = normalize_base_path(read_xml_value(CONFIG_DIR / "radarr" / "config.xml", "UrlBase", ""))
    sonarr_url_base = normalize_base_path(read_xml_value(CONFIG_DIR / "sonarr" / "config.xml", "UrlBase", ""))

    sonarr_settings = _ombi_request("/api/v1/Settings/sonarr", ombi_api_key)
    if not isinstance(sonarr_settings, dict):
        return {"ok": False, "error": "Ombi Sonarr settings payload is invalid"}
    sonarr_settings["enabled"] = True
    sonarr_settings["apiKey"] = sonarr_api_key
    sonarr_settings["ip"] = "localhost"
    sonarr_settings["port"] = 8989
    sonarr_settings["ssl"] = False
    sonarr_settings["subDir"] = sonarr_url_base
    sonarr_result = _ombi_request("/api/v1/Settings/sonarr", ombi_api_key, method="POST", payload=sonarr_settings)

    radarr_bundle = _ombi_request("/api/v1/Settings/radarr", ombi_api_key)
    if not isinstance(radarr_bundle, dict):
        return {"ok": False, "error": "Ombi Radarr settings payload is invalid"}
    radarr_settings = dict(radarr_bundle.get("radarr") or {})
    if not radarr_settings:
        return {"ok": False, "error": "Ombi Radarr settings object missing"}
    radarr_settings["enabled"] = True
    radarr_settings["apiKey"] = radarr_api_key
    radarr_settings["ip"] = "localhost"
    radarr_settings["port"] = 7878
    radarr_settings["ssl"] = False
    radarr_settings["subDir"] = radarr_url_base
    radarr_settings["defaultRootPath"] = radarr_root_path
    radarr_bundle["radarr"] = radarr_settings
    radarr_result = _ombi_request("/api/v1/Settings/radarr", ombi_api_key, method="POST", payload=radarr_bundle)

    return {
        "ok": True,
        "ombiApiKeyFound": True,
        "sonarr": sonarr_result,
        "radarr": radarr_result,
    }


def ombi_data() -> dict:
    url_base = normalize_base_path(OMBI_URL_BASE)
    base_url = f"http://{OMBI_HOST}:3579{url_base}"
    status_payload = fetch_json(f"{base_url}/api/v1/Status")
    about_payload = fetch_json(f"{base_url}/api/v1/Settings/about")
    status_ok = bool(status_payload == 200 or status_payload == "200")
    request_stats_payload = fetch_json_optional(f"{base_url}/api/v1/Request/stats", default=None) or {}
    request_count_payload = fetch_json_optional(f"{base_url}/api/v1/Request/count", default=None) or {}
    if not isinstance(request_stats_payload, dict):
        request_stats_payload = {}
    if not isinstance(request_count_payload, dict):
        request_count_payload = {}

    pending = parse_int(request_stats_payload.get("pending"))
    if pending is None:
        pending = parse_int(request_count_payload.get("pending"))

    approved = parse_int(request_stats_payload.get("approved"))
    if approved is None:
        approved = parse_int(request_count_payload.get("approved"))

    available = parse_int(request_stats_payload.get("available"))
    if available is None:
        available = parse_int(request_count_payload.get("available"))

    total = parse_int(request_stats_payload.get("total") or request_stats_payload.get("totalRequests"))
    if total is None:
        total = parse_int(request_count_payload.get("total") or request_count_payload.get("totalRequests"))
    if total is None:
        total = sum(value for value in (pending, approved, available) if value is not None)

    movies = parse_int(request_stats_payload.get("movies") or request_stats_payload.get("movie"))
    if movies is None:
        movies = parse_int(request_count_payload.get("movies") or request_count_payload.get("movie"))

    tv = parse_int(request_stats_payload.get("tv") or request_stats_payload.get("tvShows"))
    if tv is None:
        tv = parse_int(request_count_payload.get("tv") or request_count_payload.get("tvShows"))

    request_stats = {
        "total": total,
        "movies": movies,
        "tv": tv,
        "pending": pending,
        "approved": approved,
        "available": available,
    }

    return {
        "online": True,
        "url": f"http://localhost:3579{url_base or '/'}",
        "system": {
            "version": about_payload.get("version", "unknown"),
            "branch": about_payload.get("branch") or "-",
            "frameworkDescription": about_payload.get("frameworkDescription", "-"),
            "osDescription": about_payload.get("osDescription", "-"),
            "storagePath": about_payload.get("storagePath", "-"),
            "ombiDatabaseType": about_payload.get("ombiDatabaseType", "-"),
            "statusOk": status_ok,
            "requestEngine": about_payload.get("requestEngine", "-"),
            "commit": about_payload.get("commit", "-"),
        },
        "stats": request_stats,
        "queueCount": 0,
        "queue": [],
        "history": [],
        "libraryCount": 0,
        "library": [],
    }




