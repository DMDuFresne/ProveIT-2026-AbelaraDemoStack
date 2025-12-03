# Cloudflare Tunnel Configuration - Historian

This stack uses Cloudflare Tunnel for secure external access without exposing ports.

## Setup Instructions

1. Create a tunnel in your Cloudflare Zero Trust dashboard
2. Get the tunnel token
3. Add the token to your `.env` file as `HISTORIAN_CLOUDFLARE_TUNNEL_TOKEN`

## Public Hostname Configuration

Configure the following public hostnames in the Cloudflare dashboard:

| Subdomain | Domain | Service |
|-----------|--------|---------|
| explorer.historian | yourdomain.com | http://historian-nginx:80 |

## Notes

- The nginx service handles routing based on subdomain
- Cloudflare tunnel connects to the nginx service on the routing-network
- No ports need to be exposed to the public internet
- The Historian TCP port (4511) is not exposed via Cloudflare - use direct connection or VPN for collector access
