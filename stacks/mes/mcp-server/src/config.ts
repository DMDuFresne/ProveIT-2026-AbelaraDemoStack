/**
 * Configuration module for the MES MCP Server
 * Parses and validates environment variables
 */

import { z } from 'zod';

const configSchema = z.object({
  databaseUrl: z.string().url().describe('PostgreSQL connection URL'),
  schemaRefreshIntervalMs: z.number().int().positive().default(3600000),
  queryTimeoutMs: z.number().int().positive().default(30000),
  maxRows: z.number().int().positive().default(1000),
  exposedSchemas: z.array(z.string()).default(['mes_core', 'mes_audit', 'mes_custom']),
});

export type Config = z.infer<typeof configSchema>;

function parseExposedSchemas(value: string | undefined): string[] {
  if (!value) return ['mes_core', 'mes_audit', 'mes_custom'];
  return value.split(',').map(s => s.trim()).filter(Boolean);
}

export function loadConfig(): Config {
  const databaseUrl = process.env.DATABASE_URL;

  if (!databaseUrl) {
    throw new Error('DATABASE_URL environment variable is required');
  }

  const rawConfig = {
    databaseUrl,
    schemaRefreshIntervalMs: process.env.SCHEMA_REFRESH_INTERVAL_MS
      ? parseInt(process.env.SCHEMA_REFRESH_INTERVAL_MS, 10)
      : undefined,
    queryTimeoutMs: process.env.QUERY_TIMEOUT_MS
      ? parseInt(process.env.QUERY_TIMEOUT_MS, 10)
      : undefined,
    maxRows: process.env.MAX_ROWS
      ? parseInt(process.env.MAX_ROWS, 10)
      : undefined,
    exposedSchemas: parseExposedSchemas(process.env.EXPOSED_SCHEMAS),
  };

  const result = configSchema.safeParse(rawConfig);

  if (!result.success) {
    const errors = result.error.issues
      .map(issue => `${issue.path.join('.')}: ${issue.message}`)
      .join(', ');
    throw new Error(`Invalid configuration: ${errors}`);
  }

  return result.data;
}

// Singleton config instance
let cachedConfig: Config | null = null;

export function getConfig(): Config {
  if (!cachedConfig) {
    cachedConfig = loadConfig();
  }
  return cachedConfig;
}
