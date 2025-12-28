# SoulScan Architecture & Deployment Guide

A comprehensive guide explaining how SoulScan works, from the core logic to production deployment.

---

## Table of Contents

1. [What is SoulScan?](#1-what-is-soulscan)
2. [System Architecture](#2-system-architecture)
3. [Core Components](#3-core-components)
4. [Data Flow](#4-data-flow)
5. [The Arbitrage Algorithm](#5-the-arbitrage-algorithm)
6. [DEX Math Explained](#6-dex-math-explained)
7. [Supervisor Pattern](#7-supervisor-pattern)
8. [Systemd Deployment](#8-systemd-deployment)
9. [Debugging Guide](#9-debugging-guide)

---

## 1. What is SoulScan?

SoulScan is a **CEX/DEX arbitrage detection system** for Solana. It finds price differences between:

- **CEX** (Centralized Exchanges): Binance, Bybit, OKX, etc.
- **DEX** (Decentralized Exchanges): Jupiter aggregator using Orca, Raydium, Meteora pools

### Example Arbitrage Opportunity

```
CEX (Bybit):  Sell 100 SOL → Get $17,500 USDC
DEX (Jupiter): Buy 100 SOL ← Pay $17,400 USDC
                            ─────────────────
                            Profit: $100
```

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           SoulScan System                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐    ┌──────────────────┐    ┌───────────────┐ │
│  │  DataFetchers    │    │   SoulEngine     │    │    Output     │ │
│  │                  │    │                  │    │               │ │
│  │ • MetadataFetcher│───▶│ • SmartRouter    │───▶│ Redis Stream  │ │
│  │ • StateFetcher   │    │ • Scanner        │    │ "saniya"      │ │
│  │                  │    │ • Comparer       │    │               │ │
│  └────────┬─────────┘    └────────┬─────────┘    └───────────────┘ │
│           │                       │                                  │
│           ▼                       ▼                                  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                         Redis Database                          ││
│  │  • Pool Metadata (snapshot:metadata:*)                          ││
│  │  • Pool State (snapshot:state:*)                                ││
│  │  • Cold Paths (snapshot:cold_path)                              ││
│  │  • CEX Orderbooks (stream:orderbook:*)                          ││
│  │  • CEX Token Mappings (contract addresses)                      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 DataFetchers

**Purpose**: Collect data from external sources and store in Redis.

| Component | Source | Redis Key | Update Frequency |
|-----------|--------|-----------|------------------|
| `MetadataFetcher` | DEX APIs | `snapshot:metadata:{market}:{version}` | ~60s |
| `StateFetcher` | Solana RPC | `snapshot:state:{market}:{version}` | ~1-5s |

**Files**:
- `src/DataFetcher/api_clients/` - API-based metadata fetchers
- `src/DataFetcher/rpc_clients/` - RPC-based state fetchers

### 3.2 OnlineSmartRouter

**Purpose**: Pre-compute the best swap routes for all token pairs.

**How it works**:
1. Build a graph of all pools (tokens = nodes, pools = edges)
2. Find all paths from Token A to Quote (USDC)
3. Test each path with sample amounts
4. Save top N routes as "cold paths" to Redis

**Why "cold"?** The routes are computed ahead of time (cold), not during the hot path of arbitrage detection.

**File**: `src/SoulEngine/SmartRouter/OnlineSmartRouter.py`

### 3.3 Scanner (SoulScanner)

**Purpose**: Distribute tokens to worker processes for comparison.

**How it works**:
1. Get list of tokens that exist on both CEX and DEX
2. Break into chunks
3. Push chunks to a multiprocessing queue
4. Workers (Comparers) process each chunk

**File**: `src/SoulEngine/SoulScanner.py`

### 3.4 Comparer (SoulComparer)

**Purpose**: The brain - finds arbitrage opportunities.

**How it works**:
1. For each token, get CEX orderbook
2. For each order level, simulate the trade:
   - CEX→DEX: Buy on CEX (asks), sell on DEX
   - DEX→CEX: Buy on DEX, sell on CEX (bids)
3. If profit > threshold, emit signal

**File**: `src/SoulEngine/SoulComparer.py`

---

## 4. Data Flow

```
                    ┌─────────────────────────────────────────┐
                    │           External Sources              │
                    └─────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  DEX APIs     │           │  Solana RPC   │           │  CEX Streams  │
│  (Pool info)  │           │  (Pool state) │           │  (Orderbooks) │
└───────┬───────┘           └───────┬───────┘           └───────┬───────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│ MetadataFetcher           │ StateFetcher  │           │ StreamWatcher │
│               │           │               │           │  (separate)   │
└───────┬───────┘           └───────┬───────┘           └───────┬───────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
                          ┌───────────────────┐
                          │       Redis       │
                          └─────────┬─────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
          ┌───────────────┐               ┌───────────────┐
          │ OnlineSmartRouter             │   Scanner     │
          │ (Computes routes)│            │ (Distributes) │
          └───────┬─────────┘             └───────┬───────┘
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                        ┌───────────────────┐
                        │     Comparer      │
                        │ (Finds arb opps)  │
                        └─────────┬─────────┘
                                  │
                                  ▼
                        ┌───────────────────┐
                        │  Signal Stream    │
                        │  Redis: "saniya"  │
                        └───────────────────┘
```

---

## 5. The Arbitrage Algorithm

### Two Directions

**CEX→DEX (ASK side)**: Buy tokens cheaply on CEX, sell for more on DEX

```python
# Simplified logic from SoulComparer._probe_cex_ask()

for order in orderbook:  # CEX asks (sell orders)
    price = order[0]     # e.g., $175 per token
    amount = order[1]    # e.g., 100 tokens
    
    # How much we pay on CEX
    cex_cost = amount * price  # 100 * $175 = $17,500
    
    # How much we get on DEX (after aggregator fee)
    dex_amount = amount * (1 - 0.005)  # 99.5 tokens after 0.5% fee
    dex_revenue = smart_router.ExactSwap(dex_amount)  # e.g., $17,600
    
    profit = dex_revenue - cex_cost  # $17,600 - $17,500 = $100
```

**DEX→CEX (BID side)**: Buy tokens on DEX, sell for more on CEX

```python
# Simplified logic from SoulComparer._probe_cex_bid()

for order in orderbook:  # CEX bids (buy orders)
    price = order[0]     # e.g., $176 per token
    amount = order[1]    # e.g., 100 tokens
    
    # How much we get on CEX
    cex_revenue = amount * price  # 100 * $176 = $17,600
    
    # How much we need to spend on DEX
    # SmartRouter gives us "how many USDC to get 100 tokens"
    dex_cost_raw = smart_router.ExactSwap(amount, is_input=False)
    dex_cost = dex_cost_raw / (1 - 0.005)  # Add aggregator fee
    
    profit = cex_revenue - dex_cost
```

### Greedy vs Probe Strategy

**Greedy**: Try consuming the entire order level first (fast)
**Probe**: If greedy fails, try 10%, 20%, ... 100% of the level (thorough)

```python
# Greedy test (fast)
if greedy_profit > current_best:
    accept_full_level()
    continue  # Skip probe

# Probe test (if greedy fails)
for fraction in [0.1, 0.2, 0.3, ... 1.0]:
    partial_profit = calculate(level * fraction)
    if partial_profit < current_best:
        break  # Stop, profit is decreasing
    current_best = partial_profit
```

---

## 6. DEX Math Explained

### Why SmartRouter?

Jupiter is an aggregator that finds the best route. SoulScan replicates this logic locally using:

1. **Pool State**: Current reserves, liquidity, tick data
2. **Pool Metadata**: Fee rates, token decimals, pool type
3. **Math**: Uniswap V2/V3 formulas

### Uniswap V2 (AMM) Math

Used by: Raydium AMM

```
x * y = k (constant product)

If giving Δx tokens:
  Δy = (y * Δx) / (x + Δx)
```

**File**: `src/DEX/Swap/swap_manager/OriginSwap/UniswapV2Swap.py`

### Uniswap V3 (CLMM) Math

Used by: Orca CLMM, Raydium CLMM, Meteora DLMM

```
More complex - uses concentrated liquidity in price ranges (ticks)

Price = sqrt(P) where P = y/x
Each tick represents a 0.01% price change
Liquidity is only active within tick ranges
```

**File**: `src/DEX/Swap/swap_manager/OriginSwap/UniswapV3Swap.py`

### Example Calculation

```python
# From RayAmmSwap.raydium_amm_swap()

reserves_x = 1_000_000  # 1M token X in pool
reserves_y = 175_000    # 175K USDC in pool (price = $0.175)

delta_x = 10_000        # Selling 10K tokens

# Constant product: x * y = k
# (x + Δx) * (y - Δy) = x * y
# Δy = y * Δx / (x + Δx)

delta_y = (175_000 * 10_000) / (1_000_000 + 10_000)
delta_y = 1_732.67 USDC  # We receive this
```

---

## 7. Supervisor Pattern

### Why Supervisors?

Processes can crash. Supervisors ensure they restart automatically.

```
┌─────────────────────────────────────────────────────────────────┐
│                      OSRSupervisor                               │
│  (The "parent" that watches and restarts if child dies)         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    while True:                                                   │
│        if osr_worker is None:                                   │
│            osr_worker = start_new_worker()                      │
│        elif not osr_worker.is_alive():                          │
│            osr_worker.join()        # Clean up dead process     │
│            osr_worker = start_new_worker()  # Restart           │
│        time.sleep(5)                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ manages
                              ▼
            ┌─────────────────────────────────────┐
            │         OnlineSmartRouter           │
            │  (The actual worker doing the job)  │
            └─────────────────────────────────────┘
```

### Multiprocessing in Python

**Why `spawn` instead of `fork`?**

```python
multiprocessing.set_start_method('spawn')
```

| Method | How it works | Problem |
|--------|--------------|---------|
| `fork` | Copy parent process memory | Redis connections, file handles get corrupted |
| `spawn` | Start fresh Python process | Clean slate, safe for network connections |

---

## 8. Systemd Deployment

### What is systemd?

Linux's service manager. Controls:
- Starting/stopping services
- Auto-restart on crash
- Boot-time startup
- Service dependencies

### Service File Anatomy

```ini
[Unit]
Description=SoulScan Scanner
After=redis.service          # Wait for Redis to start first
Requires=redis.service       # Fail if Redis isn't running

[Service]
Type=simple                  # Just run the command directly
User=soulscan               # Security: run as unprivileged user
WorkingDirectory=/opt/soulscan
Environment="PYTHONPATH=/opt/soulscan"  # So Python can find modules

ExecStart=/opt/soulscan/venv/bin/python -m scripts.run_supervisor scanner

Restart=always              # ALWAYS restart if it crashes
RestartSec=5               # Wait 5 seconds before restarting

StandardOutput=journal     # Send stdout to journald (logging)
StandardError=journal      # Send stderr to journald

[Install]
WantedBy=multi-user.target  # Start when system reaches multi-user mode (normal boot)
```

### Service Dependency Chain

```
                    [redis.service]
                          │
                          ▼
            [soulscan-metadata-fetcher]
                          │
                          ▼
              [soulscan-state-fetcher]
                          │
                          ▼
             [soulscan-smart-router]
                          │
                          ▼
               [soulscan-scanner]
```

`After=` means "start after this", `Requires=` means "fail if this fails"

### Common Commands

```bash
# Start a service
sudo systemctl start soulscan-scanner

# Stop a service
sudo systemctl stop soulscan-scanner

# Restart a service
sudo systemctl restart soulscan-scanner

# Check status
systemctl status soulscan-scanner

# Enable auto-start on boot
sudo systemctl enable soulscan-scanner

# Disable auto-start
sudo systemctl disable soulscan-scanner

# View live logs
journalctl -u soulscan-scanner -f

# View recent logs
journalctl -u soulscan-scanner --since "1 hour ago"

# Reload after editing .service files
sudo systemctl daemon-reload
```

### The install.sh Script Explained

```bash
#!/bin/bash

# 1. Create a dedicated user (security best practice)
#    - No home directory (--no-create-home)
#    - Can't login (--shell /bin/false)
#    - System user (--system)
useradd --system --no-create-home --shell /bin/false soulscan

# 2. Create installation directory
mkdir -p /opt/soulscan
mkdir -p /opt/soulscan/LogFolder

# 3. Copy project files
cp -r . /opt/soulscan/
chown -R soulscan:soulscan /opt/soulscan  # Give ownership

# 4. Create virtual environment (isolate dependencies)
python3 -m venv /opt/soulscan/venv
/opt/soulscan/venv/bin/pip install -r requirements.txt

# 5. Install systemd services
cp systemd/*.service /etc/systemd/system/
systemctl daemon-reload  # Tell systemd to reload its config

# 6. Enable services (start on boot)
systemctl enable soulscan-metadata-fetcher
systemctl enable soulscan-state-fetcher
systemctl enable soulscan-smart-router
systemctl enable soulscan-scanner
```

---

## 9. Debugging Guide

### Service Won't Start

```bash
# Check the error
journalctl -u soulscan-scanner -n 100

# Common issues:
# - "ModuleNotFoundError" → Check PYTHONPATH and venv
# - "Permission denied" → Check file ownership
# - "Address already in use" → Another instance running
```

### Test Manually

```bash
# Run as the service user to see exact behavior
sudo -u soulscan /opt/soulscan/venv/bin/python -m scripts.run_supervisor scanner
```

### Check Redis Data

```bash
redis-cli

# Check if metadata exists
KEYS snapshot:metadata:*

# Check if state is fresh
GET snapshot:state:meteora:dlmm
# Look at the "ts" field - should be within 5 seconds

# Check cold paths
HGETALL snapshot:cold_path
```

### Logs Locations

| Source | Location |
|--------|----------|
| systemd/journald | `journalctl -u soulscan-*` |
| Application logs | `/opt/soulscan/LogFolder/` |

### Process Monitoring

```bash
# See all SoulScan processes
ps aux | grep soulscan

# See resource usage
htop -u soulscan
```

---

## Quick Reference

| Component | Purpose | Config Location |
|-----------|---------|-----------------|
| MetadataFetcher | Pool info from APIs | `src/DataFetcher/api_clients/` |
| StateFetcher | Live pool state | `src/DataFetcher/rpc_clients/` |
| OnlineSmartRouter | Pre-compute routes | `OnlineSmartRouterConfigScheme` |
| Scanner | Distribute work | `ScannerConfig` |
| Comparer | Find arbitrage | `config.MINIMAL_PROFIT` |

| Key Config | Location | Default |
|------------|----------|---------|
| Redis | `src/Config/config.py` | `localhost:6379` |
| Min Profit | `config.MINIMAL_PROFIT` | `100` USD |
| Swap Fee | `config.SWAPPER_FEE` | `0.005` (0.5%) |
| State Decay | `config.POOL_STATE_DECAY_TIME` | `5` seconds |
