# ProveIT 2026 Demo Stack - Deployment Commands

This directory contains all the individual stacks for the ProveIT 2026 Demo Stack. Use the commands below to deploy each stack individually.

## Prerequisites

- Docker Desktop 4.x+ or Docker Engine with Docker Compose v2.x+
- All `.env` files configured (copy from `.env.example` files)
- **Core stack must be deployed first** (creates shared networks and central database)

## Navigate to Stacks Directory

```bash
cd /portainer/Files/AppData/Config/FileBrowser/ProveIT-2026-AbelaraDemoStack/stacks
```

## Start Each Stack Individually

**Important:** Start the **Core** stack first, as it creates shared networks and the central database.

### 1. Core Stack (MUST START FIRST)
```bash
cd core
docker compose up -d
docker compose ps
cd ..
```

### 2. MES Stack
```bash
cd mes
docker compose up -d
docker compose ps
cd ..
```

### 3. SCADA Stack
```bash
cd scada
docker compose up -d
docker compose ps
cd ..
```

### 4. Edge Stack
```bash
cd edge
docker compose up -d
docker compose ps
cd ..
```

### 5. Historian Stack
```bash
cd historian
docker compose up -d
docker compose ps
cd ..
```

### 6. Analytics Stack
```bash
cd analytics
docker compose up -d
docker compose ps
cd ..
```

### 7. Monitoring Stack
```bash
cd monitoring
docker compose up -d
docker compose ps
cd ..
```

### 8. Utility Stack
```bash
cd utility
docker compose up -d
docker compose ps
cd ..
```

## Stop Each Stack Individually

**Important:** Stop dependent stacks first, then stop the **Core** stack last (as it contains shared networks).

### 1. Utility Stack
```bash
cd utility
docker compose down
cd ..
```

### 2. Monitoring Stack
```bash
cd monitoring
docker compose down
cd ..
```

### 3. Analytics Stack
```bash
cd analytics
docker compose down
cd ..
```

### 4. Historian Stack
```bash
cd historian
docker compose down
cd ..
```

### 5. Edge Stack
```bash
cd edge
docker compose down
cd ..
```

### 6. SCADA Stack
```bash
cd scada
docker compose down
cd ..
```

### 7. MES Stack
```bash
cd mes
docker compose down
cd ..
```

### 8. Core Stack (STOP LAST)
```bash
cd core
docker compose down
cd ..
```

## All-in-One Deployment Script

Run this sequence to deploy all stacks in order:

```bash
# Navigate to stacks directory
cd /portainer/Files/AppData/Config/FileBrowser/ProveIT-2026-AbelaraDemoStack/stacks

# Start Core first (required)
cd core && docker compose up -d && docker compose ps && cd ..

# Start remaining stacks (can be done in parallel, but shown sequentially)
cd mes && docker compose up -d && docker compose ps && cd ..
cd scada && docker compose up -d && docker compose ps && cd ..
cd edge && docker compose up -d && docker compose ps && cd ..
cd historian && docker compose up -d && docker compose ps && cd ..
cd analytics && docker compose up -d && docker compose ps && cd ..
cd monitoring && docker compose up -d && docker compose ps && cd ..
cd utility && docker compose up -d && docker compose ps && cd ..
```

## All-in-One Shutdown Script

Run this sequence to stop all stacks in reverse order (dependent stacks first, Core last):

```bash
# Navigate to stacks directory
cd /portainer/Files/AppData/Config/FileBrowser/ProveIT-2026-AbelaraDemoStack/stacks

# Stop dependent stacks first (can be done in parallel, but shown sequentially)
cd utility && docker compose down && cd ..
cd monitoring && docker compose down && cd ..
cd analytics && docker compose down && cd ..
cd historian && docker compose down && cd ..
cd edge && docker compose down && cd ..
cd scada && docker compose down && cd ..
cd mes && docker compose down && cd ..

# Stop Core last (contains shared networks)
cd core && docker compose down && cd ..
```

## Check All Stacks Status

```bash
# From the stacks directory, check all stacks
for stack in core mes scada edge historian analytics monitoring utility; do
    echo "=== $stack ==="
    cd $stack && docker compose ps && cd ..
done
```

## Stop All Stacks (Quick Script)

**Note:** This stops all stacks in parallel. For graceful shutdown, use the individual stop commands above (stop dependent stacks first, Core last).

```bash
# From the stacks directory
for stack in utility monitoring analytics historian edge scada mes core; do
    echo "Stopping $stack..."
    cd $stack && docker compose down && cd ..
done
```

## Stack Information

| Stack | Purpose | Key Services |
|-------|---------|--------------|
| **Core** | Central data platform | PostgreSQL, PgBouncer, Ignition Gateway, Highbyte Intelligence Hub |
| **MES** | Manufacturing Execution | TimescaleDB, MES Backend Gateway, MES Frontend Gateway |
| **SCADA** | Supervisory Control | Ignition SCADA Gateway |
| **Edge** | Edge Data Collection | Ignition Edge Gateway, Fuuz Device Gateway |
| **Historian** | Time Series Data | Timebase Historian, Explorer, Collectors |
| **Analytics** | Advanced Analytics | MSSQL, Flow Software Bootstrap |
| **Monitoring** | System Health | Uptime Kuma |
| **Utility** | Developer Tools | Homepage Dashboard, DBeaver, MQTT Explorer |

## Deployment Order

The **Core stack must be deployed first** as it creates the shared networks and central database:

```
Phase 1: Core Stack
    │
    ├── Creates operations-network
    ├── Creates routing-network
    ├── PostgreSQL (shared database)
    └── PgBouncer (connection pooler)

Phase 2: Dependent Stacks (can be deployed in parallel)
    ├── MES
    ├── SCADA
    ├── Edge
    ├── Historian
    ├── Analytics
    ├── Monitoring
    └── Utility
```

## Troubleshooting

### Check if a stack is running
```bash
cd <stack-name>
docker compose ps
```

### View logs for a stack
```bash
cd <stack-name>
docker compose logs -f
```

### Restart a specific stack
```bash
cd <stack-name>
docker compose restart
```

### Stop a specific stack
```bash
cd <stack-name>
docker compose down
```

### Rebuild and restart a stack
```bash
cd <stack-name>
docker compose up -d --build
```

