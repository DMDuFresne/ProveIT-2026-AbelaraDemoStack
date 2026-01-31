/**
 * Get Relationships tool - Show FK relationships for a table or full schema
 */

import { z } from 'zod';
import { getSchemaMetadata, getTable } from '../database/schema-loader.js';

export const getRelationshipsToolName = 'get_relationships';

export const getRelationshipsToolSchema = z.object({
  table: z
    .string()
    .optional()
    .describe('Specific table name (optional - if omitted, shows all relationships)'),
  schema: z
    .string()
    .default('mes_core')
    .describe('Schema name (default: mes_core)'),
  format: z
    .enum(['text', 'mermaid'])
    .default('text')
    .describe('Output format: text or mermaid diagram (default: text)'),
});

export type GetRelationshipsToolInput = z.infer<typeof getRelationshipsToolSchema>;

export function getGetRelationshipsToolDefinition() {
  return {
    name: getRelationshipsToolName,
    description: `Show foreign key relationships between tables.

Can show:
- Relationships for a specific table (incoming and outgoing FKs)
- All relationships in a schema (overview)

Output formats:
- text: Human-readable list of relationships
- mermaid: Mermaid ER diagram syntax for visualization

Useful for understanding how tables connect and planning JOINs.`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        table: {
          type: 'string',
          description: 'Specific table name (optional - if omitted, shows all relationships)',
        },
        schema: {
          type: 'string',
          description: 'Schema name (default: mes_core)',
          default: 'mes_core',
        },
        format: {
          type: 'string',
          enum: ['text', 'mermaid'],
          description: 'Output format: text or mermaid diagram (default: text)',
          default: 'text',
        },
      },
      required: [],
    },
  };
}

interface Relationship {
  fromSchema: string;
  fromTable: string;
  fromColumn: string;
  toSchema: string;
  toTable: string;
  toColumn: string;
}

export async function executeGetRelationshipsTool(
  input: GetRelationshipsToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    const schemaName = input.schema || 'mes_core';
    const format = input.format || 'text';
    const metadata = await getSchemaMetadata();

    // Collect all relationships
    const relationships: Relationship[] = [];
    const allTables = [...metadata.tables, ...metadata.views];

    for (const table of allTables) {
      if (table.schemaName.toLowerCase() !== schemaName.toLowerCase()) continue;

      for (const col of table.columns) {
        if (col.isForeignKey && col.foreignKeyTable && col.foreignKeyColumn) {
          // Parse schema.table format
          const [fkSchema, fkTable] = col.foreignKeyTable.includes('.')
            ? col.foreignKeyTable.split('.')
            : [schemaName, col.foreignKeyTable];

          relationships.push({
            fromSchema: table.schemaName,
            fromTable: table.tableName,
            fromColumn: col.columnName,
            toSchema: fkSchema,
            toTable: fkTable,
            toColumn: col.foreignKeyColumn,
          });
        }
      }
    }

    // Filter for specific table if requested
    let filtered = relationships;
    if (input.table) {
      const tableLower = input.table.toLowerCase();
      filtered = relationships.filter(
        r =>
          r.fromTable.toLowerCase() === tableLower ||
          r.toTable.toLowerCase() === tableLower
      );

      if (filtered.length === 0) {
        // Check if table exists
        const tableInfo = await getTable(schemaName, input.table);
        if (!tableInfo) {
          return {
            content: [
              {
                type: 'text',
                text: `Table ${schemaName}.${input.table} not found.`,
              },
            ],
          };
        }
        return {
          content: [
            {
              type: 'text',
              text: `Table ${schemaName}.${input.table} has no foreign key relationships.`,
            },
          ],
        };
      }
    }

    if (format === 'mermaid') {
      return {
        content: [{ type: 'text', text: generateMermaidDiagram(filtered, input.table) }],
      };
    } else {
      return {
        content: [{ type: 'text', text: generateTextOutput(filtered, input.table) }],
      };
    }
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      content: [
        {
          type: 'text',
          text: `Error getting relationships: ${errorMessage}`,
        },
      ],
    };
  }
}

function generateTextOutput(relationships: Relationship[], targetTable?: string): string {
  const lines: string[] = [];

  if (targetTable) {
    lines.push(`## Relationships for ${targetTable}\n`);

    const outgoing = relationships.filter(
      r => r.fromTable.toLowerCase() === targetTable.toLowerCase()
    );
    const incoming = relationships.filter(
      r => r.toTable.toLowerCase() === targetTable.toLowerCase()
    );

    if (outgoing.length > 0) {
      lines.push('### Outgoing (this table references)');
      for (const rel of outgoing) {
        lines.push(`- **${rel.fromColumn}** → ${rel.toTable}.${rel.toColumn}`);
      }
      lines.push('');
    }

    if (incoming.length > 0) {
      lines.push('### Incoming (referenced by)');
      for (const rel of incoming) {
        lines.push(`- ${rel.fromTable}.**${rel.fromColumn}** → this.${rel.toColumn}`);
      }
      lines.push('');
    }
  } else {
    lines.push('## All Foreign Key Relationships\n');

    // Group by from table
    const grouped = new Map<string, Relationship[]>();
    for (const rel of relationships) {
      if (!grouped.has(rel.fromTable)) {
        grouped.set(rel.fromTable, []);
      }
      grouped.get(rel.fromTable)!.push(rel);
    }

    for (const [table, rels] of Array.from(grouped.entries()).sort()) {
      lines.push(`### ${table}`);
      for (const rel of rels) {
        lines.push(`- ${rel.fromColumn} → ${rel.toTable}.${rel.toColumn}`);
      }
      lines.push('');
    }
  }

  return lines.join('\n');
}

function generateMermaidDiagram(relationships: Relationship[], targetTable?: string): string {
  const lines: string[] = [];
  lines.push('```mermaid');
  lines.push('erDiagram');

  // Collect unique tables
  const tables = new Set<string>();
  for (const rel of relationships) {
    tables.add(rel.fromTable);
    tables.add(rel.toTable);
  }

  // Add relationships
  for (const rel of relationships) {
    // Mermaid ER syntax: TABLE1 ||--o{ TABLE2 : "relationship"
    // ||--o{ means one-to-many (most FK relationships)
    lines.push(`    ${rel.toTable} ||--o{ ${rel.fromTable} : "${rel.fromColumn}"`);
  }

  lines.push('```');

  if (targetTable) {
    lines.push(`\n*Showing relationships for ${targetTable}*`);
  } else {
    lines.push(`\n*Showing ${relationships.length} relationships across ${tables.size} tables*`);
  }

  return lines.join('\n');
}
