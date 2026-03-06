import json
import mimetypes

from http.server import SimpleHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.parse import unquote

from .config import IMAGES_DIR, STATIC_DIR
from .integrations import (
    build_admin_payload,
    build_dashboard_payload,
    build_sab_payload,
    perform_container_action,
    set_sab_paths,
)
from .settings import get_settings_status, save_settings


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _send_json(self, payload: dict, status_code: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
            if isinstance(payload, dict):
                return payload
            return {}
        except json.JSONDecodeError:
            return {}

    def _redirect(self, location: str, status_code: int = 302):
        self.send_response(status_code)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _serve_dashboard_image(self):
        raw_path = unquote(self.path.split("?", 1)[0])
        image_rel = raw_path[len("/images/") :].strip("/")
        if not image_rel:
            self.send_error(404, "Image not found")
            return

        base = IMAGES_DIR.resolve()
        image_path = (base / image_rel).resolve()
        try:
            image_path.relative_to(base)
        except ValueError:
            self.send_error(403, "Forbidden")
            return

        if not image_path.exists() or not image_path.is_file():
            self.send_error(404, "Image not found")
            return

        content_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
        body = image_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/settings":
            self.path = "/settings.html"
            super().do_GET()
            return

        if path == "/setup":
            self._redirect("/settings")
            return

        if path == "/api/settings":
            self._send_json(get_settings_status())
            return

        if path == "/healthz":
            self._send_json({"ok": True})
            return

        if path.startswith("/images/"):
            self._serve_dashboard_image()
            return

        if path == "/api/dashboard":
            self._send_json(build_dashboard_payload())
            return

        if path == "/api/sab":
            self._send_json(build_sab_payload())
            return

        if path == "/api/admin":
            self._send_json(build_admin_payload())
            return

        super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        payload = self._read_json_body()

        if path == "/api/settings/save":
            result = save_settings(payload)
            status_code = 200 if result.get("ok") else 400
            self._send_json(result, status_code=status_code)
            return

        try:
            if path == "/api/manage/container":
                service_name = str(payload.get("service") or "").strip().lower()
                action = str(payload.get("action") or "").strip().lower()
                if not service_name or not action:
                    self._send_json({"ok": False, "error": "Missing 'service' or 'action'"}, status_code=400)
                    return
                result = perform_container_action(service_name, action)
                status_code = 200 if result.get("ok") else 400
                self._send_json(result, status_code=status_code)
                return

            if path == "/api/manage/sab-paths":
                download_dir = payload.get("downloadDir")
                complete_dir = payload.get("completeDir")
                if download_dir is None and complete_dir is None:
                    self._send_json({"ok": False, "error": "Provide 'downloadDir' and/or 'completeDir'"}, status_code=400)
                    return
                result = set_sab_paths(
                    str(download_dir).strip() if download_dir is not None else None,
                    str(complete_dir).strip() if complete_dir is not None else None,
                )
                status_code = 200 if result.get("ok") else 400
                self._send_json(result, status_code=status_code)
                return

            self._send_json({"ok": False, "error": f"Unknown POST endpoint: {path}"}, status_code=404)
        except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
            self._send_json({"ok": False, "error": str(exc)}, status_code=500)
