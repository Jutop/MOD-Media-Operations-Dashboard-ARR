# MOD - Media Operations Dashboard (ARR)

<p align="center">
  <img src="dashboard_app/static/images/MOD_logo.png" alt="MOD Media Operations Dashboard Logo" width="640">
</p>

Web dashboard to monitor and operate a VPN-routed ARR stack:
- Gluetun
- SABnzbd
- Sonarr
- Radarr
- Ombi

## Quick Start

### 1) Prerequisites
- Docker
- Docker Compose
- A valid WireGuard config file

### 2) Configure Environment
- Copy `.env.example` to `.env`
- Edit `.env` values as needed
- Set `VPN_WG_CONF` to your local WireGuard file path

### 3) Start the Stack
```bash
docker compose up -d --build
```

### 4) Open the Dashboard
- Dashboard URL: `http://localhost:8090` (default from `.env.example`)

## Important Notes
- Do not commit secrets (`.env`, WireGuard configs, API keys).
- Runtime data (`config/`, `media/`, `backups/`) is intentionally gitignored.
- First startup may take a bit while containers initialize.

## Main Files
- `docker-compose.yml`
- `.env.example`
- `dashboard_app/`

