/**
 * Refresh Schema tool - Force reload of schema metadata cache
 */

import { z } from 'zod';
import { forceRefreshSchema } from '../database/schema-loader.js';

export const refreshSchemaToolName = 'refresh_schema';

export const refreshSchemaToolSchema = z.object({});

export type RefreshSchemaToolInput = z.infer<typeof refreshSchemaToolSchema>;

export function getRefreshSchemaToolDefinition() {
  return {
    name: refreshSchemaToolName,
    description: `Force refresh of the database schema cache.

Use this tool when:
- You've made DDL changes (CREATE/ALTER/DROP) and need to see them immediately
- The cached schema information seems outdated
- You want to verify the current database structure

Returns a summary of the refreshed schema including counts of tables, views, and functions.`,
    inputSchema: {
      type: 'object' as const,
      properties: {},
      required: [],
    },
  };
}

export async function executeRefreshSchemaTool(
  _input: RefreshSchemaToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    const startTime = Date.now();
    const summary = await forceRefreshSchema();
    const elapsed = Date.now() - startTime;

    const lines: string[] = [
      '# Schema Refresh Complete',
      '',
      `Refresh time: ${elapsed}ms`,
      '',
      '## Summary',
      `- **Tables**: ${summary.tables}`,
      `- **Views**: ${summary.views}`,
      `- **Functions**: ${summary.functions}`,
      '',
      '## Database Context',
      `- Database comment: ${summary.hasDatabaseComment ? 'Yes' : 'No'}`,
      `- Schemas with comments: ${summary.schemasWithComments}`,
    ];

    return {
      content: [{ type: 'text', text: lines.join('\n') }],
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      content: [
        {
          type: 'text',
          text: `Error refreshing schema: ${errorMessage}`,
        },
      ],
    };
  }
}
