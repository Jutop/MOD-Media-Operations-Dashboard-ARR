import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .config import (
    COMMAND_TIMEOUT_SECONDS,
    DOCKER_BIN,
    DOWNLOADS_DIR,
    HTTP_TIMEOUT_SECONDS,
    MEDIA_ROOT_DIR,
    QUEUE_LIMIT,
)


def parse_iso_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    raw = str(value).strip()
    if not raw:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def normalize_records(payload) -> tuple[list, int]:
    if isinstance(payload, list):
        return payload, len(payload)
    if isinstance(payload, dict):
        records = payload.get("records", [])
        if not isinstance(records, list):
            records = []
        return records, int(payload.get("totalRecords", len(records)))
    return [], 0


def bool_label(value) -> str:
    return "Yes" if bool(value) else "No"


def normalize_base_path(raw_value: str) -> str:
    if not raw_value:
        return ""
    value = raw_value.strip()
    if not value:
        return ""
    if not value.startswith("/"):
        value = "/" + value
    return value.rstrip("/")


def read_xml_value(file_path: Path, tag: str, default: str = "") -> str:
    if not file_path.exists():
        return default
    try:
        tree = ElementTree.parse(file_path)
        node = tree.getroot().find(tag)
        if node is None or node.text is None:
            return default
        return node.text.strip()
    except ElementTree.ParseError:
        return default


def read_ini_value(file_path: Path, key: str, default: str = "") -> str:
    if not file_path.exists():
        return default
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*)\s*$", re.IGNORECASE)
    for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return default


def fetch_json(url: str, headers: dict | None = None) -> dict:
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))


def fetch_json_optional(url: str, headers: dict | None = None, default=None):
    try:
        return fetch_json(url, headers=headers)
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
        return default


def run_command(args: list[str], timeout_seconds: int = COMMAND_TIMEOUT_SECONDS) -> dict:
    try:
        process = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "ok": process.returncode == 0,
            "code": process.returncode,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "code": None,
            "stdout": "",
            "stderr": str(exc),
        }


def docker_available() -> dict:
    result = run_command([DOCKER_BIN, "version", "--format", "{{json .}}"], timeout_seconds=8)
    if not result["ok"]:
        return {"ok": False, "error": result["stderr"] or result["stdout"] or "Docker unavailable"}
    return {"ok": True, "error": None}


def bytes_to_gb(value: int | float | None) -> str:
    if value in (None, ""):
        return "-"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{num / (1024 ** 3):.2f} GB"


def parse_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_int(value) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def bytes_to_human(value: int | float | None) -> str:
    if value in (None, ""):
        return "-"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "-"
    units = ("B", "KB", "MB", "GB", "TB")
    index = 0
    while num >= 1024 and index < len(units) - 1:
        num /= 1024
        index += 1
    return f"{num:.2f} {units[index]}"


def calculate_progress(total: float | None, remaining: float | None) -> int | None:
    if total is None or remaining is None or total <= 0:
        return None
    progress = ((total - remaining) / total) * 100
    return max(0, min(100, round(progress)))


def summarize_health(payload) -> dict:
    records, _ = normalize_records(payload)
    warnings = 0
    errors = 0
    items = []

    for entry in records:
        level = str(entry.get("type") or entry.get("severity") or "").strip().lower()
        if level in {"error", "fatal"}:
            errors += 1
        elif level in {"warning", "warn"}:
            warnings += 1

    for entry in records[:QUEUE_LIMIT]:
        items.append(
            {
                "source": entry.get("sourceName") or entry.get("source") or "-",
                "type": str(entry.get("type") or entry.get("severity") or "info"),
                "message": entry.get("message") or "-",
            }
        )

    return {
        "totalIssues": len(records),
        "warnings": warnings,
        "errors": errors,
        "items": items,
    }


def summarize_diskspace(payload) -> dict:
    records, _ = normalize_records(payload)
    volumes = []
    total_space = 0
    free_space = 0

    for item in records:
        total = parse_int(item.get("totalSpace")) or 0
        free = parse_int(item.get("freeSpace")) or 0
        path_value = item.get("path") or item.get("label") or "-"
        total_space += total
        free_space += free
        volumes.append(
            {
                "path": str(path_value),
                "free": bytes_to_human(free),
                "total": bytes_to_human(total),
                "freePercent": round((free / total) * 100, 1) if total > 0 else None,
            }
        )

    used_percent = round(((total_space - free_space) / total_space) * 100, 1) if total_space > 0 else None
    return {
        "volumeCount": len(volumes),
        "totalSpace": total_space,
        "freeSpace": free_space,
        "totalReadable": bytes_to_human(total_space),
        "freeReadable": bytes_to_human(free_space),
        "usedPercent": used_percent,
        "volumes": volumes[:QUEUE_LIMIT],
    }


def summarize_rootfolders_space(payload) -> dict:
    records, _ = normalize_records(payload)
    volumes = []
    free_values: list[int] = []
    total_values: list[int] = []

    for item in records:
        free = parse_int(item.get("freeSpace"))
        total = parse_int(item.get("totalSpace"))
        path_value = item.get("path") or item.get("label") or "-"
        accessible = bool(item.get("accessible", True))
        if not accessible:
            continue

        # ARR can report freeSpace but not totalSpace for some mounts; fallback to host/container fs stats.
        path_text = str(path_value)
        if (free is None or total is None or total <= 0) and path_text.startswith("/"):
            try:
                usage = shutil.disk_usage(path_text)
                total = int(usage.total)
                free = int(usage.free)
            except OSError:
                pass

        if free is not None:
            free_values.append(free)
        if total is not None and total > 0:
            total_values.append(total)

        volumes.append(
            {
                "path": str(path_value),
                "free": bytes_to_human(free),
                "total": bytes_to_human(total),
                "freePercent": round((free / total) * 100, 1) if (free is not None and total and total > 0) else None,
            }
        )

    if not volumes:
        return {
            "volumeCount": 0,
            "totalSpace": 0,
            "freeSpace": 0,
            "totalReadable": "-",
            "freeReadable": "-",
            "usedPercent": None,
            "volumes": [],
        }

    # Conservative free-space indicator: lowest free space across configured root folders.
    free_space = min(free_values) if free_values else 0
    total_space = max(total_values) if total_values else 0
    used_percent = round(((total_space - free_space) / total_space) * 100, 1) if total_space > 0 else None
    return {
        "volumeCount": len(volumes),
        "totalSpace": total_space,
        "freeSpace": free_space,
        "totalReadable": bytes_to_human(total_space) if total_space > 0 else "-",
        "freeReadable": bytes_to_human(free_space),
        "usedPercent": used_percent,
        "volumes": volumes[:QUEUE_LIMIT],
    }


def summarize_arr_queue(records: list[dict]) -> tuple[list[dict], dict]:
    downloading = 0
    importing = 0
    warnings = 0
    queue_items = []

    for item in records:
        status = str(item.get("status", "")).lower()
        tracked_state = str(item.get("trackedDownloadState", "")).lower()
        tracked_status = str(item.get("trackedDownloadStatus", "")).lower()
        if status in {"downloading", "queued"}:
            downloading += 1
        if "import" in tracked_state or tracked_state == "downloaded":
            importing += 1
        if tracked_status in {"warning", "failed"} or status in {"warning", "failed"}:
            warnings += 1

    for item in records[:QUEUE_LIMIT]:
        size_value = parse_float(item.get("size"))
        left_value = parse_float(item.get("sizeleft"))
        queue_items.append(
            {
                "title": item.get("title") or item.get("outputPath") or "Unknown",
                "status": item.get("status", "-"),
                "trackedState": item.get("trackedDownloadState", "-"),
                "trackedStatus": item.get("trackedDownloadStatus", "-"),
                "protocol": item.get("protocol", "-"),
                "indexer": item.get("indexer", "-"),
                "timeLeft": item.get("timeleft", "-"),
                "estCompletion": format_iso_date(item.get("estimatedCompletionTime")),
                "size": bytes_to_human(size_value),
                "sizeLeft": bytes_to_human(left_value),
                "progressPercent": calculate_progress(size_value, left_value),
            }
        )

    summary = {
        "downloading": downloading,
        "importing": importing,
        "warnings": warnings,
    }
    return queue_items, summary


def format_file_mtime(file_path: Path) -> str:
    try:
        dt = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
        return dt.date().isoformat()
    except OSError:
        return "-"


def collect_ready_files(category_hints: tuple[str, ...], limit: int = QUEUE_LIMIT) -> list[dict]:
    complete_dir = DOWNLOADS_DIR / "complete"

    candidates: list[Path] = []
    seen: set[str] = set()

    scan_roots: list[Path] = []
    if complete_dir.exists():
        for hint in category_hints:
            scan_roots.append(complete_dir / hint)
    # Fallback root locations for already-imported library items.
    for hint in category_hints:
        scan_roots.append(MEDIA_ROOT_DIR / hint)

    for root in scan_roots:
        if not root.exists():
            continue
        for item in root.iterdir():
            if item.name.startswith("."):
                continue
            key = str(item.resolve())
            if key in seen:
                continue
            seen.add(key)
            candidates.append(item)

    # Last fallback: use direct children from complete dir.
    if not candidates:
        if complete_dir.exists():
            for item in complete_dir.iterdir():
                if item.name.startswith("."):
                    continue
                candidates.append(item)

    candidates.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)

    return [
        {
            "title": file_path.name if file_path.is_dir() else file_path.stem,
            "status": "Ready",
            "date": format_file_mtime(file_path),
            "path": str(file_path).replace("\\", "/"),
        }
        for file_path in candidates[:limit]
    ]


def format_iso_date(value: str | None) -> str:
    if not value:
        return "-"
    dt = parse_iso_datetime(value)
    if dt == datetime.min.replace(tzinfo=timezone.utc):
        return str(value)[:10]
    return dt.date().isoformat()


def is_ready_to_move(item: dict) -> bool:
    status = str(item.get("status", "")).lower()
    tracked_state = str(item.get("trackedDownloadState", "")).lower()
    if status == "completed":
        return True
    if "import" in tracked_state or tracked_state == "downloaded":
        return True
    return False
