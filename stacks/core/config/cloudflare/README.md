# Cloudflare Tunnel Configuration Guide

This guide explains how to configure Cloudflare Tunnel for external access to the CORE stack services via dedicated subdomains (e.g., `core.yourdomain.com`).

## Overview

The Cloudflare Tunnel provides secure external access to services without opening firewall ports. Each stack has its own tunnel, enabling both local development (multiple tunnels on one machine) and production deployment (one tunnel per VM).

### Routing Architecture

**Three-Tier Architecture:**
1. **Cloudflare Tunnel:** Routes by subdomain to Nginx reverse proxy
2. **Nginx Reverse Proxy:** Handles path-based routing and path rewriting
3. **Backend Services:** Receive requests at root paths (as designed)

**Pattern:** `{stack}.yourdomain.com/{service-name}`

**Example:**
- `core.yourdomain.com/ignition` → Nginx → Core Ignition Gateway (at `/`)
- `core.yourdomain.com/highbyte` → Nginx → Highbyte Intelligence Hub (at `/`)
- `mes.yourdomain.com/backend` → Nginx → MES Backend Gateway (at `/`)
- `mes.yourdomain.com/frontend` → Nginx → MES Frontend Gateway (at `/`)

**Why Nginx?**
- Cloudflare Tunnel forwards full paths (e.g., `/ignition/*` → backend receives `/ignition/...`)
- Most services expect root paths (`/`)
- Nginx strips path prefixes before forwarding, enabling clean URLs

## Subdomain Naming Convention

**Pattern:** `{stack-name}.yourdomain.com`

Each stack gets its own subdomain based on the stack directory name. This provides a scalable, intuitive naming scheme.

### Current Stacks & Service Routes

Each stack uses path-based routing to expose multiple services under a single subdomain.

| Stack | Subdomain | Services & Paths | Example URLs |
|-------|-----------|-------------------|--------------|
| `core` | `core.yourdomain.com` | `/ignition/*` → Ignition Gateway<br>`/highbyte/*` → Highbyte Intelligence Hub | `https://core.yourdomain.com/ignition`<br>`https://core.yourdomain.com/highbyte` |
| `scada` | `scada.yourdomain.com` | `/ignition/*` → SCADA Ignition Gateway | `https://scada.yourdomain.com/ignition` |
| `mes` | `mes.yourdomain.com` | `/backend/*` → MES Backend Gateway<br>`/frontend/*` → MES Frontend Gateway | `https://mes.yourdomain.com/backend`<br>`https://mes.yourdomain.com/frontend` |
| `utility` | `utility.yourdomain.com` | `/homepage/*` → Homepage Dashboard<br>`/dbeaver/*` → DBeaver Database Tool<br>`/mqtt-explorer/*` → MQTT Explorer | `https://utility.yourdomain.com/homepage`<br>`https://utility.yourdomain.com/dbeaver`<br>`https://utility.yourdomain.com/mqtt-explorer` |
| `analytics` | `analytics.yourdomain.com` | *(configure based on services)* | |
| `historian` | `historian.yourdomain.com` | *(configure based on services)* | |
| `monitoring` | `monitoring.yourdomain.com` | *(configure based on services)* | |
| `edge-gateway` | `edge-gateway.yourdomain.com` | *(configure based on services)* | |
| `edge-enterprise` | `edge-enterprise.yourdomain.com` | *(configure based on services)* | |

### Path-Based Routing Pattern

**Pattern:** `{stack}.yourdomain.com/{service-name}/*`

- **Subdomain** = Stack name (one per stack)
- **Path** = Service name (multiple services per stack)
- Each tunnel routes multiple services using path matching

**Service Naming Convention:**
- Use lowercase, hyphenated service names
- Match the service's logical purpose (e.g., `ignition`, `highbyte`, `backend`, `frontend`)
- Keep paths intuitive and consistent across stacks

### Adding New Stacks

When adding a new stack:

1. **Use the stack directory name as the subdomain** (lowercase, hyphenated)
   - Stack directory: `my-new-stack` → Subdomain: `my-new-stack.yourdomain.com`
   - Stack directory: `dataLake` → Subdomain: `datalake.yourdomain.com` (normalize to lowercase)

2. **Create DNS record:**
   - **Type:** CNAME
   - **Name:** `{stack-name}` (match directory name, lowercase)
   - **Target:** `{tunnel-id}.cfargotunnel.com`
   - **Proxy status:** Proxied (orange cloud)

3. **Configure routes for each service:**
   - Add one route per service with a unique path prefix
   - Use intuitive service names (e.g., `/ignition/*`, `/api/*`, `/web/*`)
   - Add catch-all route (`/*` → `http_status:404`) as the last route
   - Routes are evaluated top-to-bottom, so specific paths must come first

4. **Naming consistency:**
   - Keep subdomains lowercase
   - Use hyphens for multi-word stacks (e.g., `edge-gateway`, not `edgegateway`)
   - Match the stack directory name exactly (normalized to lowercase)
   - Use lowercase, hyphenated service paths (e.g., `/mqtt-explorer/*`, not `/MQTTExplorer/*`)

**Example:** Adding a new `data-lake` stack with two services:
- Directory: `stacks/data-lake/`
- Subdomain: `data-lake.yourdomain.com`
- DNS Name: `data-lake`
- Tunnel Name: `proveit-data-lake-tunnel`
- **Routes:**
  - `/api/*` → `https://data-lake-api:8080`
  - `/dashboard/*` → `http://data-lake-dashboard:3000`
  - `/*` → `http_status:404` (catch-all, last)

## Prerequisites

- Cloudflare account with Zero Trust access
- Domain `yourdomain.com` managed by Cloudflare
- Docker Compose stack running

## Configuration Steps

### 1. Create Cloudflare Tunnel

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **Zero Trust** → **Networks** → **Tunnels**
3. Click **"Create a tunnel"**
4. Select **"Cloudflared"** as the connector type
5. Name the tunnel: `proveit-core-tunnel` (or your preference)
6. Click **"Save tunnel"**
7. **Copy the tunnel token** - you'll need this for the `CORE_CLOUDFLARE_TUNNEL_TOKEN` environment variable

### 2. Configure DNS Record

1. Navigate to **DNS** → **Records**
2. Click **"Add record"**
3. Configure:
   - **Type:** CNAME
   - **Name:** `core` (matches stack directory name - see [Subdomain Naming Convention](#subdomain-naming-convention))
   - **Target:** `[your-tunnel-id].cfargotunnel.com`
     - Replace `[your-tunnel-id]` with your actual tunnel ID (found in tunnel details)
   - **Proxy status:** Proxied (orange cloud icon)
   - **TTL:** Auto
4. Click **"Save"**

**Result:** `core.yourdomain.com` will route to this tunnel.

**Important:** Each tunnel requires its own DNS record (subdomain). Cloudflare Tunnel routes by hostname/subdomain, not by path. Follow the [Subdomain Naming Convention](#subdomain-naming-convention) for consistency.

### 3. Configure Ingress Routes

**Architecture:** Cloudflare Tunnel → Nginx Reverse Proxy → Backend Services

The stack includes an **Nginx reverse proxy** that handles path rewriting, allowing `https://core.yourdomain.com/ignition` to work correctly. Cloudflare Tunnel routes to Nginx, which strips path prefixes and forwards to the appropriate backend services.

1. Go back to **Zero Trust** → **Networks** → **Tunnels**
2. Click on your tunnel (`proveit-core-tunnel`)
3. Click **"Configure"** tab
4. Under **"Public Hostname"**, click **"Add a public hostname"**

Add routes pointing to the Nginx reverse proxy. Routes are evaluated **top-to-bottom**, so more specific paths must come before catch-all routes.

#### Route 1: All Services via Nginx (HTTP)
- **Subdomain:** `core` (match your DNS record)
- **Domain:** `yourdomain.com`
- **Path:** `/*` ⚠️ **Catch-all route**
- **Service:** `http://nginx:80`
- **Additional Settings:** None required

**How it works:**
- Cloudflare Tunnel forwards all requests (`/*`) to Nginx at `http://nginx:80`
- Nginx handles path-based routing:
  - `/ignition/*` → Strips prefix, forwards to `https://core-ignition-gateway:8043/`
  - `/highbyte/*` → Strips prefix, forwards to `http://highbyte:45245/`
  - Other paths → Returns 404

**Result:** 
- `https://core.yourdomain.com/ignition` → Core Ignition Gateway (at root `/`)
- `https://core.yourdomain.com/highbyte` → Highbyte Intelligence Hub (at root `/`)

**Important:** 
- Only one route needed - Nginx handles all path routing internally
- Nginx configuration is in `stacks/core/config/nginx/nginx.conf`
- To add new services, update the Nginx config and add new `location` blocks

### 4. Set Environment Variable

1. Copy `.env.example` to `.env` if you haven't already:
   ```bash
   cp stacks/core/.env.example stacks/core/.env
   ```

2. Edit `stacks/core/.env` and set:
   ```bash
   CORE_CLOUDFLARE_TUNNEL_TOKEN=your-actual-tunnel-token-here
   ```

3. Replace `your-actual-tunnel-token-here` with the token you copied in Step 1.

## Starting the Tunnel

After configuration, start the tunnel service:

```bash
cd stacks/core
docker-compose up -d cloudflared
```

## Verification

### Check Tunnel Status

View tunnel logs to verify connection:
```bash
docker logs proveit-core-cloudflared
```

Look for messages like:
- `Connection established`
- `Connected to Cloudflare`
- `Registered tunnel connection`

### Test Routes

1. **Core Ignition Gateway:**
   - Visit: `https://core.yourdomain.com/ignition`
   - Should load the Ignition Gateway login page

2. **Highbyte Web UI:**
   - Visit: `https://core.yourdomain.com/highbyte`
   - Should load the Highbyte interface

3. **Invalid Path (404):**
   - Visit: `https://core.yourdomain.com/invalid`
   - Should return a 404 error

## Troubleshooting

### Quick Diagnostics

1. **Check all services are running:**
   ```bash
   cd stacks/core
   docker-compose ps
   ```
   All services should show "Up" and "healthy" status.

2. **View service logs:**
   ```bash
   docker-compose logs nginx
   docker-compose logs cloudflared
   docker-compose logs core-ignition-gateway
   ```

3. **Test nginx locally:**
   ```bash
   curl http://localhost:8080/ignition/StatusPing
   curl http://localhost:8080/highbyte/
   ```

4. **Test Cloudflare Tunnel route:**
   ```bash
   curl https://core.yourdomain.com/ignition/StatusPing
   ```

### Tunnel Not Connecting

- Verify the token is correct in `.env`
- Check tunnel logs: `docker logs proveit-core-cloudflared`
- Ensure services are running: `docker-compose ps`
- Verify network connectivity: `docker network inspect operations-network`
- **Check nginx health:** Cloudflared depends on nginx being healthy

### Routes Not Working

- **Verify Cloudflare Tunnel route points to nginx:**
  - Route should be: `/*` → `http://nginx:80`
  - NOT directly to backend services
  
- Verify DNS record is proxied (orange cloud)
- Check service health: `docker-compose ps`
- Check tunnel logs for connection errors: `docker logs proveit-core-cloudflared --tail 50`

### Nginx Issues

**502 Bad Gateway:**
- Verify backend services are running: `docker-compose ps`
- Test connectivity from nginx: `docker exec proveit-core-nginx ping core-ignition-gateway`
- Check nginx logs: `docker logs proveit-core-nginx`

**Path not being stripped:**
- Verify nginx config has trailing slash in `proxy_pass`: `proxy_pass https://ignition_gateway/;`
- Test locally: `curl http://localhost:8080/ignition/StatusPing`

**For detailed troubleshooting, see:** [`config/nginx/TROUBLESHOOTING.md`](nginx/TROUBLESHOOTING.md)

### SSL/TLS Issues

**"Connection refused" or "Unable to reach the origin service" errors:**

**For HTTPS services (like Ignition Gateway):**

1. **Enable "No TLS Verify":** 
   - Go to Cloudflare Dashboard → Zero Trust → Networks → Tunnels
   - Click on your tunnel → Configure tab
   - Edit the route for `https://core-ignition-gateway:8043`
   - Under "Additional Settings", set **"No TLS Verify"** to `true` ⚠️ **REQUIRED**
   - Click Save
   - Wait 1-2 minutes for configuration to propagate

2. **Set Origin Server Name (optional but recommended):**
   - In the same route settings, set **"Origin Server Name"** to `core-ignition-gateway`
   - This helps with SNI (Server Name Indication) during SSL handshake

3. **Verify service is listening:**
   - Check Ignition Gateway logs: `docker logs core-ignition-gateway`
   - Verify service is healthy: `docker-compose ps`
   - Test from host: `curl -k https://localhost:8045/StatusPing` (should return "OK")

**For HTTP services (like Highbyte):**

- No TLS verification settings needed - HTTP services work without additional configuration
- If HTTP service fails, check:
  - Service is running: `docker-compose ps highbyte`
  - Service logs: `docker logs proveit-highbyte`
  - Network connectivity: Verify service hostname matches container name exactly

**404 Errors on Services (Path Matching Issues):**

If you get a 404 when accessing a service (e.g., `https://core.yourdomain.com/highbyte`):

1. **Verify path pattern uses wildcard:**
   - Path should be `/highbyte/*` (with `/*` at the end) to match `/highbyte` and sub-paths
   - Path `/highbyte` (without wildcard) only matches exactly `/highbyte` and may not work correctly

2. **Check if path rewrite is needed:**
   - When cloudflared forwards to `http://highbyte:45245`, it forwards the full path `/highbyte/*`
   - If the service expects paths at root (`/`), you need to configure path rewriting:
     - In Cloudflare Dashboard → Tunnel → Configure → Edit route
     - Under "Additional Settings" → Look for "Path" options
     - Configure to strip the path prefix before forwarding (e.g., strip `/highbyte` so `/highbyte/api` becomes `/api`)
   - Alternatively, test if the service accepts the prefixed path directly

3. **Test the service locally:**
   ```bash
   # Test service directly at root
   Invoke-WebRequest -Uri http://localhost:45245/
   
   # Test with path prefix (if service supports it)
   Invoke-WebRequest -Uri http://localhost:45245/highbyte
   ```

4. **Verify route order:**
   - Ensure specific routes (e.g., `/highbyte/*`) come BEFORE the catch-all `/*` route
   - Routes are evaluated top-to-bottom, first match wins

5. **Service-specific path handling:**
   - Some services (like Ignition Gateway) handle path prefixes gracefully
   - Others (like simple web apps) may need path rewriting to strip the prefix
   - Check service documentation or test locally to determine if rewriting is needed

## Services Exposed (Core Stack Example)

- **Core Ignition Gateway (HTTPS):** `https://core.yourdomain.com/ignition`
- **Highbyte Web UI (HTTP):** `https://core.yourdomain.com/highbyte`

**Note:** Services are exposed via Nginx reverse proxy which handles path rewriting. See [Current Stacks & Service Routes](#current-stacks--service-routes) for complete mapping.

## Adding New Services to a Stack

To add a new service to an existing stack (e.g., add a new service to the Core stack):

1. **Add the service** to your `docker-compose.yml` (if not already present)

2. **Update Nginx configuration** (`stacks/core/config/nginx/nginx.conf`):
   
   Add a new upstream block:
   ```nginx
   upstream new_service {
       server new-service:8080;
   }
   ```
   
   Add a new location block:
   ```nginx
   # New Service - strip /new-service prefix
   location /new-service/ {
       proxy_pass http://new_service/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_set_header X-Forwarded-Host $host;
       proxy_set_header X-Forwarded-Prefix /new-service;
   }
   
   # Redirect /new-service to /new-service/
   location = /new-service {
       return 301 /new-service/;
   }
   ```
   
   **Important:** Place specific paths (like `/new-service/`) **before** the catch-all `location /` block.

3. **Restart Nginx:**
   ```bash
   docker-compose restart nginx
   ```

4. **Verify:**
   - Visit `https://core.yourdomain.com/new-service`
   - Check Nginx logs: `docker logs proveit-core-nginx`

**Result:** The new service is accessible at `https://core.yourdomain.com/new-service` and receives requests at root path `/` (as designed).

## Services NOT Exposed

The following services remain internal-only:
- PostgreSQL (5432) - Internal database
- PgBouncer (6432) - Internal connection pooler
- Ignition Gateway port (8061) - Internal Ignition-to-Ignition communication
- Highbyte MQTT/MQTTS/OPC ports - Internal protocols
- Ignition HTTP port (8088) - Using HTTPS only

## Adding Additional Stacks

To add tunnels to other stacks (e.g., SCADA, MES), you have two options:

### Option 1: Separate Subdomains (Recommended)

Each tunnel requires its own DNS record (subdomain). This is the recommended approach for separate stacks. Follow the [Subdomain Naming Convention](#subdomain-naming-convention).

**Example: Adding SCADA Stack**

1. **Add cloudflared service** to `stacks/scada/docker-compose.yml`:
   ```yaml
   cloudflared:
     <<: *defaults
     image: cloudflare/cloudflared:latest
     container_name: proveit-scada-cloudflared
     command: tunnel --no-autoupdate run --token ${SCADA_CLOUDFLARE_TUNNEL_TOKEN}
     networks:
       - scada-network  # Use your stack's network
     depends_on:
       - scada-ignition-gateway  # Depend on your services
   ```

2. **Create separate tunnel** in Cloudflare Dashboard:
   - Name: `proveit-scada-tunnel` (pattern: `proveit-{stack-name}-tunnel`)
   - Get token → use in `stacks/scada/.env` as `SCADA_CLOUDFLARE_TUNNEL_TOKEN`

3. **Create separate DNS record**:
   - **Type:** CNAME
   - **Name:** `scada` (matches stack directory name)
   - **Target:** `[scada-tunnel-id].cfargotunnel.com`
   - **Proxy status:** Proxied (orange cloud)

4. **Add Nginx reverse proxy** to the stack's `docker-compose.yml` (see Core stack as example)

5. **Create Nginx configuration** (`stacks/{stack-name}/config/nginx/nginx.conf`) with routes for each service

6. **Configure Cloudflare Tunnel routes** (single route to Nginx):
   - **Route 1:** `/*` → `http://nginx:80` (all traffic goes to Nginx)
   
   **Nginx handles all path routing internally:**
   - `/ignition/*` → Strips prefix, forwards to backend service
   - `/service-name/*` → Strips prefix, forwards to backend service
   - Other paths → Returns 404
   
   **Note:** Each stack should have its own Nginx instance configured for that stack's services.

**Result:** 
- `scada.yourdomain.com` → SCADA stack
- `core.yourdomain.com` → Core stack
- Each stack is independently accessible via its own subdomain

### Option 2: Single Tunnel with All Routes

Use one tunnel for all stacks and configure all routes in that tunnel:

1. **Add all cloudflared services** to their respective `docker-compose.yml` files
2. **Use the same tunnel token** in all stacks (or run cloudflared in one stack that can reach all services)
3. **Configure all routes** in the same tunnel (using a single subdomain like `proveit.yourdomain.com`):
   - `/core/ignition/*` → `https://core-ignition-gateway:8043`
   - `/scada/ignition/*` → `https://scada-ignition-gateway:8046`
   - `/mes/*` → `https://mes-service:port`
   - `/*` → `http_status:404` (catch-all, must be last)

**Note:** This approach requires a reverse proxy or path-based routing within a single tunnel. The separate subdomain approach (Option 1) is recommended for better isolation and scalability.

**Note:** This requires all services to be reachable from the same Docker network or the tunnel container must be able to reach all services.

**Important:** Cloudflare Tunnel routes by hostname/subdomain, not by path. Path matching only works within a single tunnel's configuration. For separate tunnels, each needs its own DNS record.

## Security Considerations

### Current Security Posture

**✅ Secure Aspects:**
- No inbound firewall ports required (outbound-only tunnel)
- Internal services (PostgreSQL, PgBouncer) are NOT exposed externally
- Path-based routing limits exposure to specific endpoints
- Services isolated on Docker network (`operations-network`)
- Cloudflare terminates TLS/SSL externally

**⚠️ Security Concerns:**

1. **No Access Control:** Currently, anyone with the URL can access services. **CRITICAL for production.**

2. **TLS Verification Disabled:** "No TLS Verify: true" bypasses certificate validation (required for self-signed certs, but increases risk).

3. **HTTP Internal Service:** Highbyte uses HTTP internally (though Cloudflare terminates TLS externally).

4. **Token Storage:** Tunnel token stored in `.env` file (not committed, but not using secrets management).

### Recommended Security Hardening

#### 1. Configure Zero Trust Access Policies (REQUIRED for Production)

**Step 1: Create Access Application**
1. Go to **Zero Trust** → **Access** → **Applications**
2. Click **"Add an application"**
3. Select **"Self-hosted"**
4. Configure:
   - **Application name:** `ProveIT Core Services`
   - **Session duration:** `24 hours` (or your preference)
   - **Application domain:** `core.yourdomain.com`
   - **Path:** `/*` (or specific paths like `/ignition/*`)

**Step 2: Configure Authentication**
1. Under **"Policies"**, click **"Add a policy"**
2. **Policy name:** `ProveIT Access Policy`
3. **Action:** `Allow`
4. **Include:**
   - **Emails:** Add allowed email addresses or domains (e.g., `@abelara.com`)
   - **OR IP Address:** Add allowed IP ranges (e.g., `192.168.1.0/24`)
   - **OR Country:** Restrict to specific countries
5. **Require:**
   - **Email:** Select your identity provider (Google, Microsoft, etc.)
   - **OR Device Posture:** Require managed devices (optional)
6. Click **"Save policy"**

**Step 3: Apply Policy to Tunnel Routes**
1. Go to **Zero Trust** → **Networks** → **Tunnels**
2. Click on your tunnel → **Configure** tab
3. For each route (e.g., `/ignition/*`), click **"Edit"**
4. Under **"Access"**, select your application: `ProveIT Core Services`
5. Click **"Save"`

**Repeat for each stack:** Create separate Access Applications for each stack (e.g., `ProveIT SCADA Services` for `scada.yourdomain.com`)

**Result:** Users will be prompted to authenticate before accessing services.

#### 2. Improve Certificate Security (Recommended)

**Option A: Use Proper SSL Certificates**
1. Generate or obtain valid SSL certificates for Ignition Gateway
2. Configure Ignition Gateway to use these certificates
3. Remove "No TLS Verify: true" from tunnel route configuration
4. This enables full certificate validation

**Option B: Document Self-Signed Certificate Risk**
- If self-signed certificates must be used, document:
  - Why proper certificates cannot be used
  - Risk acceptance approval
  - Certificate rotation procedures
  - Monitoring for certificate changes

#### 3. Secure Tunnel Token (Production)

**Option A: Docker Secrets (Recommended)**
1. Create secret:
   ```bash
   echo "your-tunnel-token" | docker secret create core_cloudflare_tunnel_token -
   ```
2. Update `docker-compose.yml`:
   ```yaml
   cloudflared:
     secrets:
       - core_cloudflare_tunnel_token
     environment:
       CORE_CLOUDFLARE_TUNNEL_TOKEN_FILE: /run/secrets/core_cloudflare_tunnel_token
     command: tunnel --no-autoupdate run --token $(cat /run/secrets/core_cloudflare_tunnel_token)
   ```

**Option B: External Secrets Manager**
- Use HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault
- Inject secrets at runtime via environment variables or secret files

#### 4. Enable HTTPS for Internal Services (Optional but Recommended)

**For Highbyte:**
- Configure Highbyte to use HTTPS internally
- Update tunnel route from `http://highbyte:45245` to `https://highbyte:45245`
- Add "No TLS Verify: true" if using self-signed certs

**Benefits:**
- End-to-end encryption even if Docker network is compromised
- Defense in depth

#### 5. Additional Security Measures

**Rate Limiting:**
- Configure Cloudflare rate limiting rules to prevent abuse
- Go to **Security** → **WAF** → **Rate limiting rules**

**WAF Rules:**
- Enable Cloudflare WAF (Web Application Firewall)
- Configure rules to block common attack patterns

**Logging and Monitoring:**
- Enable Cloudflare Analytics to monitor access patterns
- Set up alerts for suspicious activity
- Review tunnel logs regularly: `docker logs proveit-core-cloudflared`

**Regular Security Audits:**
- Review access policies quarterly
- Rotate tunnel tokens annually or when compromised
- Audit exposed services and remove unnecessary routes
- Review and update passwords regularly

### Security Checklist

Before deploying to production, ensure:

- [ ] Zero Trust access policies configured and tested
- [ ] Strong passwords set (not defaults from `.env.example`)
- [ ] Tunnel token stored securely (secrets management)
- [ ] SSL certificates properly configured (or risk documented)
- [ ] Rate limiting enabled
- [ ] WAF rules configured
- [ ] Logging and monitoring enabled
- [ ] Access policies tested with unauthorized users
- [ ] Internal services use HTTPS where possible
- [ ] Regular security review schedule established

## Additional Resources

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare Zero Trust](https://developers.cloudflare.com/cloudflare-one/)

