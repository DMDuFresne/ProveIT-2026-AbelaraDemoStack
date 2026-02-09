# Cloudflare Tunnel Configuration - MES

This stack uses Cloudflare Tunnel for secure external access without exposing ports.

## Setup Instructions

1. Create a tunnel in your Cloudflare Zero Trust dashboard
2. Get the tunnel token
3. Add the token to your `.env` file as `MES_CLOUDFLARE_TUNNEL_TOKEN`

## Public Hostname Configuration

Configure the following public hostnames in the Cloudflare dashboard:

| Subdomain | Domain | Service | Notes |
|-----------|--------|---------|-------|
| ignition-backend.mes | abelara.cloud | http://mes-nginx:80 | Backend Ignition Gateway |
| ignition-frontend-01.mes | abelara.cloud | http://mes-nginx:80 | Frontend Ignition Gateway |
| mes.mcp | abelara.cloud | http://mes-nginx:80 | **NEW** MES MCP Server (Streamable HTTP + OAuth) |
| mes-database.mcp | abelara.cloud | http://mes-nginx:80 | **EXISTING** Legacy MCP Postgres (SSE via Supergateway) |

## MCP Servers

This stack has **two separate MCP servers**:

### 1. MES MCP Server (NEW) - `mes.mcp.abelara.cloud`

Custom MCP server with MES-specific domain context, documentation, and query examples.

| Property | Value |
|----------|-------|
| Container | `mes-mcp-server` |
| Port | 3000 |
| Transport | Streamable HTTP |
| Auth | OAuth 2.0 (optional password) |
| Endpoints | `/mcp`, `/oauth/*`, `/.well-known/*`, `/health` |

**Environment Variable:**
```bash
MES_MCP_EXTERNAL_URL=https://mes.mcp.abelara.cloud
```

**Client Configuration (.mcp.json):**
```json
{
  "mcpServers": {
    "mes": {
      "type": "streamable-http",
      "url": "https://mes.mcp.abelara.cloud/mcp"
    }
  }
}
```

### 2. Legacy MCP Postgres (EXISTING) - `mes-database.mcp.abelara.cloud`

Generic postgres MCP via Supergateway (stdio-to-SSE conversion).

| Property | Value |
|----------|-------|
| Container | `mes-mcp-postgres` |
| Port | 8000 |
| Transport | SSE (Server-Sent Events) |
| Auth | None |
| Endpoints | `/sse`, `/message` |

**Client Configuration (.mcp.json):**
```json
{
  "mcpServers": {
    "mes-database": {
      "type": "sse",
      "url": "https://mes-database.mcp.abelara.cloud/sse"
    }
  }
}
```

## Cloudflare Dashboard Settings

When adding hostnames, use these settings:

| Setting | Value |
|---------|-------|
| HTTP/2 | Enabled |
| Disable Chunked Encoding | **Disabled** (required for SSE) |

## Notes

- The nginx service handles subdomain-based routing
- Cloudflare tunnel connects to nginx on the `routing-network`
- No ports need to be exposed to the public internet
- TLS termination happens at Cloudflare edge

## Troubleshooting

### OAuth "Protected Resource Mismatch" Error (mes.mcp only)

If you see: `Protected resource http://X does not match expected http://Y`

1. Ensure `MES_MCP_EXTERNAL_URL=https://mes.mcp.abelara.cloud` (with https://)
2. Client `.mcp.json` must use the same base URL
3. Restart the MCP server after changing the env var

### SSE Connection Drops

If SSE streams disconnect unexpectedly:
1. Check Cloudflare timeout settings (increase if needed)
2. Verify nginx `proxy_read_timeout` is set high (86400s in config)
3. Check for any proxy buffering (should be disabled)
