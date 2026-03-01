from .config import OMBI_HOST, OMBI_URL_BASE
from .utils import fetch_json, fetch_json_optional, normalize_base_path, parse_int
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




