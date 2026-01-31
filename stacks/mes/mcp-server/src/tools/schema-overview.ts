/**
 * Schema Overview tool - Get complete schema as structured JSON
 */

import { z } from 'zod';
import { generateSchemaOverview } from '../descriptions/generator.js';
import { getSchemaOverviewToolDescription } from '../descriptions/generator.js';
import { getTableDescription, getFunctionDescription } from '../descriptions/generator.js';

export const schemaOverviewToolName = 'schema_overview';

export const schemaOverviewToolSchema = z.object({});

export type SchemaOverviewToolInput = z.infer<typeof schemaOverviewToolSchema>;

export function getSchemaOverviewToolDefinition() {
  return {
    name: schemaOverviewToolName,
    description: getSchemaOverviewToolDescription(),
    inputSchema: {
      type: 'object' as const,
      properties: {},
      required: [],
    },
  };
}

export async function executeSchemaOverviewTool(
  _input: SchemaOverviewToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    const schema = await generateSchemaOverview();

    // Enhance with static descriptions
    const enhancedSchema = {
      lastRefreshed: schema.lastRefreshed.toISOString(),
      tables: schema.tables.map(t => ({
        schema: t.schemaName,
        name: t.tableName,
        type: t.tableType,
        description: getTableDescription(t),
        columns: t.columns.map(c => ({
          name: c.columnName,
          type: c.dataType,
          nullable: c.isNullable,
          primaryKey: c.isPrimaryKey,
          foreignKey: c.isForeignKey
            ? { table: c.foreignKeyTable, column: c.foreignKeyColumn }
            : null,
          default: c.columnDefault,
          comment: c.comment,
        })),
      })),
      views: schema.views.map(v => ({
        schema: v.schemaName,
        name: v.tableName,
        description: getTableDescription(v),
        columns: v.columns.map(c => ({
          name: c.columnName,
          type: c.dataType,
          nullable: c.isNullable,
          comment: c.comment,
        })),
      })),
      functions: schema.functions.map(f => ({
        schema: f.schemaName,
        name: f.functionName,
        description: getFunctionDescription(f),
        returnType: f.returnType,
        parameters: f.parameters.map(p => ({
          name: p.name,
          type: p.dataType,
          mode: p.mode,
          default: p.defaultValue,
        })),
        isVolatile: f.isVolatile,
      })),
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(enhancedSchema, null, 2),
        },
      ],
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      content: [
        {
          type: 'text',
          text: `Error generating schema overview: ${errorMessage}`,
        },
      ],
    };
  }
}
