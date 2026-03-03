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

## Dashboard Preview

<p align="center">
  <img src="dashboard_app/static/images/dashboard_demo.png" alt="MOD Dashboard Demo" width="1100">
</p>

## Quick Start

### 1) Prerequisites
- Docker
- Docker Compose
- A WireGuard config file from your VPN provider

### 2) Configure Environment
- Copy `.env.example` to `.env`
- Edit `.env` values as needed
- Set `VPN_WG_CONF` to your local WireGuard file path

### 2.1) WireGuard Config (Required)
- Download a WireGuard profile (`.conf`) from your VPN provider dashboard.
- Put the file in this repo, for example: `./vpn/wg0.conf`
- In `.env`, set:

```env
VPN_WG_CONF=./vpn/wg0.conf
```

- The path is relative to the project root (`docker-compose.yml` location).
- Do not commit this file (it contains private keys).
- If startup fails, check VPN logs:

```bash
docker compose logs --tail=200 gluetun
```

Quick check: a valid file usually contains sections like `[Interface]` and `[Peer]`.

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
- Required root folders are auto-created by the `init_dirs` service when you run `docker compose up`.

## Main Files
- `docker-compose.yml`
- `.env.example`
- `dashboard_app/`
