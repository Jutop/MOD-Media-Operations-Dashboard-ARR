from http.server import ThreadingHTTPServer

from .config import HOST, PORT
from .http_api import DashboardHandler


def main():
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"Dashboard server listening on http://{HOST}:{PORT}")
    server.serve_forever()
