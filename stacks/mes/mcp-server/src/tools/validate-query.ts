/**
 * Validate Query tool - Check query syntax without executing
 */

import { z } from 'zod';
import { rawQuery } from '../database/client.js';
import { containsBlockedKeywords } from '../database/client.js';

export const validateQueryToolName = 'validate_query';

export const validateQueryToolSchema = z.object({
  sql: z.string().min(1).describe('The SQL query to validate'),
});

export type ValidateQueryToolInput = z.infer<typeof validateQueryToolSchema>;

export function getValidateQueryToolDefinition() {
  return {
    name: validateQueryToolName,
    description: `Validate SQL query syntax without executing it.

Uses PostgreSQL's PREPARE statement to parse and validate the query.
Returns either:
- Success with the query plan summary
- Error with details about what's wrong (syntax errors, unknown tables, etc.)

Useful for:
- Checking query syntax before running
- Validating table and column names exist
- Catching errors early without affecting data

Only SELECT queries are allowed.`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        sql: {
          type: 'string',
          description: 'The SQL query to validate',
        },
      },
      required: ['sql'],
    },
  };
}

export async function executeValidateQueryTool(
  input: ValidateQueryToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    // Security check
    const blockedKeyword = containsBlockedKeywords(input.sql);
    if (blockedKeyword) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                valid: false,
                error: `Query contains blocked keyword: ${blockedKeyword}. Only SELECT queries are allowed.`,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    // Use EXPLAIN to validate without executing
    // This parses the query and checks table/column references
    const explainSql = `EXPLAIN (FORMAT JSON) ${input.sql}`;

    const result = await rawQuery<{ 'QUERY PLAN': unknown[] }>(explainSql);

    // Extract some useful info from the plan
    const plan = result.rows[0]?.['QUERY PLAN'];
    let planSummary = '';

    if (Array.isArray(plan) && plan.length > 0) {
      const topNode = plan[0] as { Plan?: { 'Node Type'?: string; 'Relation Name'?: string } };
      if (topNode.Plan) {
        planSummary = `Plan: ${topNode.Plan['Node Type'] || 'Unknown'}`;
        if (topNode.Plan['Relation Name']) {
          planSummary += ` on ${topNode.Plan['Relation Name']}`;
        }
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              valid: true,
              message: 'Query syntax is valid',
              planSummary: planSummary || 'Query parsed successfully',
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error occurred';

    // Parse PostgreSQL error for helpful details
    let hint = '';
    if (errorMessage.includes('does not exist')) {
      hint = 'Check table and column names for typos.';
    } else if (errorMessage.includes('syntax error')) {
      hint = 'Check SQL syntax near the indicated position.';
    } else if (errorMessage.includes('column') && errorMessage.includes('ambiguous')) {
      hint = 'Use table aliases to qualify ambiguous column names.';
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              valid: false,
              error: errorMessage,
              hint: hint || undefined,
            },
            null,
            2
          ),
        },
      ],
    };
  }
}
