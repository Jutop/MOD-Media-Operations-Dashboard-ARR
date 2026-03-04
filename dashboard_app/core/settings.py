import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError

from .arr import (
    arr_add_rootfolder,
    arr_rootfolders_data,
    arr_service_config,
    configure_arr_sab_download_client,
)
from .config import MEDIA_ROOT_DIR
from .ombi import configure_ombi_arr_integrations
from .sab import set_sab_paths

STATE_DIR = MEDIA_ROOT_DIR / ".mod"
STATE_FILE = STATE_DIR / "settings.json"
SUPPORTED_LANGUAGES = {"en", "de"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_text(value) -> str:
    return str(value or "").strip()


def _to_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = _to_text(value).lower()
    if not text:
        return default
    return text in {"1", "true", "yes", "on"}


def _normalize_path(value) -> str:
    text = _to_text(value).replace("\\", "/")
    if not text:
        return ""
    while "//" in text:
        text = text.replace("//", "/")
    if len(text) > 1 and text.endswith("/"):
        text = text.rstrip("/")
    return text


def _default_settings() -> dict:
    media_root = str(MEDIA_ROOT_DIR).replace("\\", "/").rstrip("/") or "/media"
    return {
        "language": "en",
        "mediaBasePath": media_root,
        "useBasePathDefaults": True,
        "radarrRootPath": f"{media_root}/movies",
        "sonarrRootPath": f"{media_root}/tv",
        "sabDownloadDir": f"{media_root}/downloads/incomplete",
        "sabCompleteDir": f"{media_root}/downloads/complete",
        "radarrSabCategory": "movies",
        "sonarrSabCategory": "tv",
        "autoConfigureAppLinks": True,
        "homePublicIp": "",
        "vpnExpectedIp": "",
        "vpnExpectedIps": "",
        "vpnOrgKeywords": "",
    }


def _read_raw_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def _write_raw_state(payload: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _merged_settings(raw_settings: dict | None = None) -> dict:
    defaults = _default_settings()
    settings = dict(defaults)
    source = raw_settings if isinstance(raw_settings, dict) else {}
    for key in settings:
        if key == "language":
            lang = _to_text(source.get("language")) or defaults["language"]
            settings["language"] = lang if lang in SUPPORTED_LANGUAGES else defaults["language"]
            continue
        if key in {"useBasePathDefaults", "autoConfigureAppLinks"}:
            settings[key] = _to_bool(source.get(key), defaults[key])
            continue
        if key.endswith("Path") or key.endswith("Dir"):
            settings[key] = _normalize_path(source.get(key)) or defaults[key]
            continue
        value = _to_text(source.get(key))
        settings[key] = value if value else defaults[key]
    return settings


def _apply_base_path_defaults(settings: dict) -> dict:
    if not settings.get("useBasePathDefaults", True):
        return settings
    base = _normalize_path(settings.get("mediaBasePath"))
    if not base or not base.startswith("/"):
        return settings
    settings["mediaBasePath"] = base
    settings["radarrRootPath"] = f"{base}/movies"
    settings["sonarrRootPath"] = f"{base}/tv"
    settings["sabDownloadDir"] = f"{base}/downloads/incomplete"
    settings["sabCompleteDir"] = f"{base}/downloads/complete"
    return settings


def get_settings_status() -> dict:
    raw = _read_raw_state()
    settings = _merged_settings(raw.get("settings"))
    settings = _apply_base_path_defaults(settings)
    return {
        "ok": True,
        "settings": settings,
        "savedAt": raw.get("savedAt"),
        "lastApply": raw.get("lastApply"),
    }


def _validate_settings(settings: dict) -> list[str]:
    errors: list[str] = []
    if settings.get("useBasePathDefaults", True):
        base = _normalize_path(settings.get("mediaBasePath"))
        if not base:
            errors.append("mediaBasePath is required when useBasePathDefaults is enabled")
        elif not base.startswith("/"):
            errors.append("mediaBasePath must be an absolute path")
    for key in ("radarrRootPath", "sonarrRootPath", "sabDownloadDir", "sabCompleteDir"):
        value = _normalize_path(settings.get(key))
        if not value:
            errors.append(f"{key} is required")
            continue
        if not value.startswith("/"):
            errors.append(f"{key} must be an absolute path")
    if settings.get("language") not in SUPPORTED_LANGUAGES:
        errors.append("language must be one of: en, de")
    return errors


def _ensure_directory(path_text: str) -> dict:
    try:
        Path(path_text).mkdir(parents=True, exist_ok=True)
        return {"ok": True, "path": path_text}
    except OSError as exc:
        return {"ok": False, "path": path_text, "error": str(exc)}


def _ensure_arr_root(service_name: str, path_text: str) -> dict:
    normalized = _normalize_path(path_text).lower()
    try:
        payload = arr_rootfolders_data(service_name)
        existing = {
            _normalize_path(item.get("path", "")).lower()
            for item in payload.get("folders", [])
            if _normalize_path(item.get("path", ""))
        }
        if normalized in existing:
            return {"ok": True, "service": service_name, "path": path_text, "applied": False, "reason": "already-exists"}
        add_result = arr_add_rootfolder(service_name, path_text)
        return {
            "ok": bool(add_result.get("ok")),
            "service": service_name,
            "path": path_text,
            "applied": True,
            "result": add_result,
        }
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
        try:
            payload = arr_rootfolders_data(service_name)
            existing = {
                _normalize_path(item.get("path", "")).lower()
                for item in payload.get("folders", [])
                if _normalize_path(item.get("path", ""))
            }
            if normalized in existing:
                return {
                    "ok": True,
                    "service": service_name,
                    "path": path_text,
                    "applied": False,
                    "reason": "already-exists-after-recheck",
                }
        except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, OSError):
            pass
        return {"ok": False, "service": service_name, "path": path_text, "error": str(exc)}


def _apply_sab_paths(download_dir: str, complete_dir: str) -> dict:
    try:
        result = set_sab_paths(download_dir, complete_dir)
        return {"ok": bool(result.get("ok")), "result": result}
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": str(exc)}


def _configure_arr_download_clients(settings: dict) -> dict:
    radarr_category = _to_text(settings.get("radarrSabCategory")) or "movies"
    sonarr_category = _to_text(settings.get("sonarrSabCategory")) or "tv"
    try:
        radarr = configure_arr_sab_download_client("radarr", radarr_category)
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
        radarr = {"ok": False, "error": str(exc)}
    try:
        sonarr = configure_arr_sab_download_client("sonarr", sonarr_category)
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
        sonarr = {"ok": False, "error": str(exc)}
    return {
        "ok": bool(radarr.get("ok")) and bool(sonarr.get("ok")),
        "radarr": radarr,
        "sonarr": sonarr,
    }


def _configure_ombi_links(settings: dict) -> dict:
    try:
        radarr_conf = arr_service_config("radarr")
        sonarr_conf = arr_service_config("sonarr")
        return configure_ombi_arr_integrations(
            radarr_api_key=radarr_conf.get("api_key", ""),
            sonarr_api_key=sonarr_conf.get("api_key", ""),
            radarr_root_path=settings["radarrRootPath"],
        )
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": str(exc)}


def _collect_issues(results: dict) -> tuple[list[str], list[str]]:
    blocking_errors: list[str] = []
    warnings: list[str] = []
    for key, item in results.get("filesystem", {}).items():
        if not item.get("ok"):
            blocking_errors.append(f"{key}: {item.get('error', 'unknown error')}")
    for key, item in results.get("automation", {}).items():
        if not item.get("ok"):
            warnings.append(f"{key}: {item.get('error', 'automation failed')}")
    return blocking_errors, warnings


def save_settings(raw_payload: dict) -> dict:
    settings = _merged_settings(raw_payload if isinstance(raw_payload, dict) else {})
    settings = _apply_base_path_defaults(settings)
    validation_errors = _validate_settings(settings)
    if validation_errors:
        return {
            "ok": False,
            "error": "Validation failed",
            "errors": validation_errors,
            "settings": settings,
        }

    filesystem = {
        "radarrRootPath": _ensure_directory(settings["radarrRootPath"]),
        "sonarrRootPath": _ensure_directory(settings["sonarrRootPath"]),
        "sabDownloadDir": _ensure_directory(settings["sabDownloadDir"]),
        "sabCompleteDir": _ensure_directory(settings["sabCompleteDir"]),
    }
    automation = {
        "radarrRoot": _ensure_arr_root("radarr", settings["radarrRootPath"]),
        "sonarrRoot": _ensure_arr_root("sonarr", settings["sonarrRootPath"]),
        "sabPaths": _apply_sab_paths(settings["sabDownloadDir"], settings["sabCompleteDir"]),
    }
    if settings.get("autoConfigureAppLinks", True):
        automation["arrSabClients"] = _configure_arr_download_clients(settings)
        automation["ombiArrLinks"] = _configure_ombi_links(settings)
    results = {"filesystem": filesystem, "automation": automation}
    blocking_errors, warnings = _collect_issues(results)
    ok = len(blocking_errors) == 0

    now = _now_iso()
    next_state = {
        "savedAt": now,
        "settings": settings,
        "lastApply": {
            "at": now,
            "ok": ok,
            "errors": blocking_errors,
            "warnings": warnings,
            "results": results,
        },
    }
    try:
        _write_raw_state(next_state)
    except OSError as exc:
        return {
            "ok": False,
            "error": f"Failed to persist settings: {exc}",
            "errors": blocking_errors,
            "warnings": warnings,
            "results": results,
            "settings": settings,
        }

    return {
        "ok": ok,
        "error": None if ok else "Failed to apply required settings actions",
        "errors": blocking_errors,
        "warnings": warnings,
        "results": results,
        "settings": settings,
        "savedAt": now,
    }


def get_runtime_vpn_settings() -> dict:
    raw_state = _read_raw_state()
    status = get_settings_status()
    settings = status.get("settings", {})
    use_saved_values = bool(raw_state.get("savedAt"))
    vpn_expected_ips = [item.strip() for item in _to_text(settings.get("vpnExpectedIps")).split(",") if item.strip()]
    vpn_org_keywords = [item.strip().lower() for item in _to_text(settings.get("vpnOrgKeywords")).split(",") if item.strip()]
    return {
        "useSavedValues": use_saved_values,
        "homePublicIp": _to_text(settings.get("homePublicIp")),
        "vpnExpectedIp": _to_text(settings.get("vpnExpectedIp")),
        "vpnExpectedIps": vpn_expected_ips,
        "vpnOrgKeywords": vpn_org_keywords,
    }
