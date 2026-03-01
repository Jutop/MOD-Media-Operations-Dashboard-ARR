import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
IMAGES_DIR = STATIC_DIR / "images"
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "/config"))
DOWNLOADS_DIR = Path(os.getenv("DOWNLOADS_DIR", "/downloads"))
MEDIA_ROOT_DIR = Path(os.getenv("MEDIA_ROOT_DIR", "/media"))
HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
PORT = int(os.getenv("DASHBOARD_PORT", "8081"))
RADARR_HOST = os.getenv("RADARR_HOST", "radarr").strip() or "radarr"
SONARR_HOST = os.getenv("SONARR_HOST", "sonarr").strip() or "sonarr"
SABNZBD_HOST = os.getenv("SABNZBD_HOST", "sabnzbd").strip() or "sabnzbd"
OMBI_HOST = os.getenv("OMBI_HOST", "gluetun").strip() or "gluetun"
OMBI_URL_BASE = os.getenv("OMBI_URL_BASE", "")
GLUETUN_IP_FILE = Path(os.getenv("GLUETUN_IP_FILE", "/gluetun_state/ip"))
DOCKER_BIN = os.getenv("DOCKER_BIN", "docker").strip() or "docker"

HTTP_TIMEOUT_SECONDS = 8
QUEUE_LIMIT = 10
COMMAND_TIMEOUT_SECONDS = 15
VPN_EXPECTED_IP = os.getenv("VPN_EXPECTED_IP", "").strip()
VPN_EXPECTED_IPS = [ip.strip() for ip in os.getenv("VPN_EXPECTED_IPS", "").split(",") if ip.strip()]
HOME_PUBLIC_IP = os.getenv("HOME_PUBLIC_IP", "").strip()
VPN_ORG_KEYWORDS = [item.strip().lower() for item in os.getenv("VPN_ORG_KEYWORDS", "").split(",") if item.strip()]
IP_PROVIDERS = (
    "https://api.ipify.org?format=json",
    "https://ifconfig.co/json",
    "https://ipinfo.io/json",
)
IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts", ".m2ts", ".wmv"}
MANAGED_CONTAINERS = {
    "gluetun": "gluetun",
    "sabnzbd": "sabnzbd",
    "sonarr": "sonarr",
    "radarr": "radarr",
    "ombi": "ombi",
    "dashboard": "media-dashboard",
}
ALLOWED_CONTAINER_ACTIONS = {"start", "stop", "restart"}
