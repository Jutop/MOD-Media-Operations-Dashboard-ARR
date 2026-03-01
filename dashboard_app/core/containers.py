import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .arr import arr_service_config
from .config import ALLOWED_CONTAINER_ACTIONS, DOCKER_BIN, MANAGED_CONTAINERS, OMBI_HOST, OMBI_URL_BASE, PORT
from .sab import sab_service_config
from .utils import docker_available, fetch_json, normalize_base_path, run_command
def synthetic_service_health(service_name: str) -> str | None:
    try:
        if service_name == "radarr":
            conf = arr_service_config("radarr")
            headers = {"X-Api-Key": conf["api_key"]}
            _ = fetch_json(f"{conf['base_url']}/api/v3/system/status", headers=headers)
            return "healthy"

        if service_name == "sonarr":
            conf = arr_service_config("sonarr")
            headers = {"X-Api-Key": conf["api_key"]}
            _ = fetch_json(f"{conf['base_url']}/api/v3/system/status", headers=headers)
            return "healthy"

        if service_name == "sabnzbd":
            conf = sab_service_config()
            query = urlencode(
                {
                    "mode": "queue",
                    "output": "json",
                    "limit": "1",
                    "apikey": conf["api_key"],
                }
            )
            payload = fetch_json(f"{conf['base_url']}/api?{query}")
            return "healthy" if isinstance(payload, dict) and "queue" in payload else "unhealthy"

        if service_name == "ombi":
            url_base = normalize_base_path(OMBI_URL_BASE)
            base_url = f"http://{OMBI_HOST}:3579{url_base}"
            status_payload = fetch_json(f"{base_url}/api/v1/Status")
            return "healthy" if status_payload in (200, "200") else "unhealthy"

        if service_name == "dashboard":
            payload = fetch_json(f"http://127.0.0.1:{PORT}/healthz")
            return "healthy" if bool(payload.get("ok")) else "unhealthy"
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, OSError, KeyError):
        return "unhealthy"
    return None




def container_states() -> dict:
    docker_state = docker_available()
    if not docker_state["ok"]:
        return {
            "ok": False,
            "error": docker_state["error"],
            "containers": {},
        }

    statuses: dict[str, dict] = {}
    for service_name, container_name in MANAGED_CONTAINERS.items():
        result = run_command([DOCKER_BIN, "container", "inspect", "--format", "{{json .State}}", container_name], timeout_seconds=8)
        if not result["ok"]:
            statuses[service_name] = {
                "container": container_name,
                "exists": False,
                "running": False,
                "status": "missing",
                "health": None,
                "startedAt": None,
                "error": result["stderr"] or result["stdout"] or "Container not found",
            }
            continue

        state_payload = {}
        try:
            state_payload = json.loads(result["stdout"])
        except json.JSONDecodeError:
            state_payload = {}
        health = state_payload.get("Health", {})
        health_status = health.get("Status") if isinstance(health, dict) else None
        if not health_status and bool(state_payload.get("Running")):
            health_status = synthetic_service_health(service_name)
        statuses[service_name] = {
            "container": container_name,
            "exists": True,
            "running": bool(state_payload.get("Running")),
            "status": state_payload.get("Status", "unknown"),
            "health": health_status,
            "startedAt": state_payload.get("StartedAt"),
            "error": None,
        }
    return {
        "ok": True,
        "error": None,
        "containers": statuses,
    }



def perform_container_action(service_name: str, action: str) -> dict:
    if action not in ALLOWED_CONTAINER_ACTIONS:
        return {"ok": False, "error": f"Action '{action}' is not allowed"}
    container_name = MANAGED_CONTAINERS.get(service_name)
    if not container_name:
        return {"ok": False, "error": f"Service '{service_name}' is not managed"}
    if service_name == "gluetun" and action == "stop":
        return {"ok": False, "error": "Stopping 'gluetun' is blocked by policy"}

    docker_state = docker_available()
    if not docker_state["ok"]:
        return {"ok": False, "error": docker_state["error"]}

    result = run_command([DOCKER_BIN, "container", action, container_name], timeout_seconds=20)
    return {
        "ok": result["ok"],
        "service": service_name,
        "container": container_name,
        "action": action,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "code": result["code"],
    }




