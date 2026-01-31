/**
 * Explain Query tool - Run EXPLAIN ANALYZE on a query
 */

import { z } from 'zod';
import { rawQuery } from '../database/client.js';
import { containsBlockedKeywords } from '../database/client.js';

export const explainQueryToolName = 'explain_query';

export const explainQueryToolSchema = z.object({
  sql: z.string().min(1).describe('The SQL SELECT query to explain'),
  analyze: z
    .boolean()
    .default(false)
    .describe('Run EXPLAIN ANALYZE (actually executes query, default: false)'),
});

export type ExplainQueryToolInput = z.infer<typeof explainQueryToolSchema>;

export function getExplainQueryToolDefinition() {
  return {
    name: explainQueryToolName,
    description: `Run EXPLAIN on a SQL query to show the execution plan.

Useful for:
- Understanding how PostgreSQL will execute a query
- Identifying missing indexes
- Optimizing slow queries
- Seeing estimated vs actual row counts (with analyze=true)

Options:
- analyze=false (default): Shows plan without executing
- analyze=true: Executes query and shows actual timings

Only SELECT queries are allowed.`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        sql: {
          type: 'string',
          description: 'The SQL SELECT query to explain',
        },
        analyze: {
          type: 'boolean',
          description: 'Run EXPLAIN ANALYZE (actually executes query, default: false)',
          default: false,
        },
      },
      required: ['sql'],
    },
  };
}

export async function executeExplainQueryTool(
  input: ExplainQueryToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    // Security check
    const blockedKeyword = containsBlockedKeywords(input.sql);
    if (blockedKeyword) {
      return {
        content: [
          {
            type: 'text',
            text: `Query contains blocked keyword: ${blockedKeyword}. Only SELECT queries are allowed.`,
          },
        ],
      };
    }

    // Build EXPLAIN command
    const explainType = input.analyze ? 'EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)' : 'EXPLAIN (FORMAT TEXT)';
    const explainSql = `${explainType} ${input.sql}`;

    const result = await rawQuery<{ 'QUERY PLAN': string }>(explainSql);

    const plan = result.rows.map(r => r['QUERY PLAN']).join('\n');

    const lines: string[] = [];
    lines.push(`## Query Execution Plan${input.analyze ? ' (with ANALYZE)' : ''}`);
    lines.push('');
    lines.push('```');
    lines.push(plan);
    lines.push('```');

    if (input.analyze) {
      lines.push('');
      lines.push('*Note: ANALYZE actually executed the query to measure real timings.*');
    }

    // Add helpful tips based on plan content
    const tips: string[] = [];
    if (plan.includes('Seq Scan')) {
      tips.push('- **Seq Scan detected**: Consider adding an index if this table is large');
    }
    if (plan.includes('Sort') && !plan.includes('Index Scan')) {
      tips.push('- **Sort without index**: Consider adding an index on the ORDER BY columns');
    }
    if (plan.includes('Nested Loop') && plan.includes('rows=')) {
      tips.push('- **Nested Loop**: Check if JOIN conditions have proper indexes');
    }

    if (tips.length > 0) {
      lines.push('');
      lines.push('### Optimization Tips');
      lines.push(...tips);
    }

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
          text: `Error explaining query: ${errorMessage}`,
        },
      ],
    };
  }
}
