# Cloudflare Tunnel Configuration - Historian

This stack uses Cloudflare Tunnel for secure external access without exposing ports.

## Setup Instructions

1. Create a tunnel in your Cloudflare Zero Trust dashboard
2. Get the tunnel token
3. Add the token to your `.env` file as `HISTORIAN_CLOUDFLARE_TUNNEL_TOKEN`

## Public Hostname Configuration

Configure the following public hostnames in the Cloudflare dashboard:

| Subdomain | Domain | Service | Description | Access Policy |
|-----------|--------|---------|-------------|---------------|
| historian.historian | abelara.cloud | http://historian-nginx:80 | Timebase Historian Database Config + MCP | **Recommended** (protect UI access) |
| explorer.historian | abelara.cloud | http://historian-nginx:80 | Timebase Explorer Web Interface | **Recommended** (protect UI access) |
| timebase.mcp | abelara.cloud | http://historian-nginx:80 | Historian MCP Server (dedicated subdomain) | **None** (allow programmatic access) |

## Public URLs

Once configured, the following URLs will be available:

- **Timebase Historian**: https://historian.historian.abelara.cloud
- **Timebase Historian MCP (dedicated subdomain)**: https://timebase.mcp.abelara.cloud (SSE optimized, no Access Policy required)
- **Timebase Historian MCP (path-based)**: https://historian.historian.abelara.cloud/mcp (SSE optimized, no Access Policy required)
- **Timebase Explorer**: https://explorer.historian.abelara.cloud

## Security Configuration

### Access Policies

**Recommended Setup:**
- **`*.historian.abelara.cloud`** (historian.historian, explorer.historian): Apply Cloudflare Access policies to protect UI access
- **`timebase.mcp.abelara.cloud`**: **No Access Policy** - Keep open for programmatic MCP client access

This allows you to:
- Secure the Historian and Explorer web UIs with Cloudflare Access authentication
- Keep the MCP endpoint accessible without authentication barriers for MCP clients and integrations
- Use a dedicated subdomain (`timebase.mcp`) that's separate from the protected `*.historian` subdomains

### MCP Endpoint Configuration

The MCP endpoint (`timebase.mcp.abelara.cloud`) is configured to work through Cloudflare Tunnel with Server-Sent Events (SSE) optimization:
- **No Access Policy Required**: MCP endpoint should remain accessible without Cloudflare Access policies for programmatic access
- **SSE Optimized**: Nginx is configured to disable buffering for MCP endpoints to support long-lived SSE connections
- **Direct Access Also Available**: MCP endpoints are also accessible directly via exposed ports if needed

## Notes

- All traffic routes through nginx which handles subdomain-based routing
- Cloudflare tunnel connects to the nginx service on the routing-network
- No ports need to be exposed to the public internet
- Nginx routes requests to the appropriate backend service based on the Host header
