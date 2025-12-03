# Cloudflare Tunnel Configuration - Monitoring

This stack uses Cloudflare Tunnel for secure external access without exposing ports.

## Setup Instructions

1. Create a tunnel in your Cloudflare Zero Trust dashboard
2. Get the tunnel token
3. Add the token to your `.env` file as `MONITORING_CLOUDFLARE_TUNNEL_TOKEN`

## Public Hostname Configuration

Configure the following public hostnames in the Cloudflare dashboard:

| Subdomain | Domain | Service |
|-----------|--------|---------|
| uptime.monitoring | yourdomain.com | http://monitoring-nginx:80 |

## Notes

- The nginx service handles routing based on subdomain
- Cloudflare tunnel connects to the nginx service on the routing-network
- No ports need to be exposed to the public internet
