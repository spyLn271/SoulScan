# SoulScan Systemd Deployment

## Quick Install

```bash
# On your Linux server
cd /path/to/SoulScan
sudo bash install.sh
```

## Services

| Service | Description |
|---------|-------------|
| `soulscan-metadata-fetcher` | Fetches pool metadata from DEX APIs |
| `soulscan-state-fetcher` | Fetches live pool state via RPC |
| `soulscan-smart-router` | Computes optimal swap routes |
| `soulscan-scanner` | Scans for CEX/DEX arbitrage |

## Commands

```bash
# Start all services
sudo systemctl start soulscan-{metadata-fetcher,state-fetcher,smart-router,scanner}

# Stop all services
sudo systemctl stop soulscan-{metadata-fetcher,state-fetcher,smart-router,scanner}

# Check status
systemctl status soulscan-*

# View logs (live)
journalctl -u soulscan-scanner -f

# View all SoulScan logs
journalctl -u 'soulscan-*' --since "1 hour ago"
```

## Prerequisites

- Redis server running on `localhost:6379`
- Python 3.10+
- CEX orderbook streams (separate service)

## File Locations

| Path | Description |
|------|-------------|
| `/opt/soulscan/` | Installation directory |
| `/opt/soulscan/LogFolder/` | Application logs |
| `/etc/systemd/system/soulscan-*.service` | Service files |

## Customization

Edit `/etc/systemd/system/soulscan-*.service` to change:
- `User` / `Group` - Run as different user
- `WorkingDirectory` - Different install path
- `Environment` - Add env vars (e.g., `SOLANA_RPC_ENDPOINT`)

After editing:
```bash
sudo systemctl daemon-reload
sudo systemctl restart soulscan-scanner
```
