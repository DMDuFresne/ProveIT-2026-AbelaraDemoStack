/**
 * Tool exports and registry
 */

// Import all tool definitions and executors
import {
  queryToolName,
  queryToolSchema,
  getQueryToolDefinition,
  executeQueryTool,
} from './query.js';

import {
  listTablesToolName,
  listTablesToolSchema,
  getListTablesToolDefinition,
  executeListTablesTool,
} from './list-tables.js';

import {
  listFunctionsToolName,
  listFunctionsToolSchema,
  getListFunctionsToolDefinition,
  executeListFunctionsTool,
} from './list-functions.js';

import {
  describeTableToolName,
  describeTableToolSchema,
  getDescribeTableToolDefinition,
  executeDescribeTableTool,
} from './describe-table.js';

import {
  schemaOverviewToolName,
  schemaOverviewToolSchema,
  getSchemaOverviewToolDefinition,
  executeSchemaOverviewTool,
} from './schema-overview.js';

import {
  getSampleDataToolName,
  getSampleDataToolSchema,
  getGetSampleDataToolDefinition,
  executeGetSampleDataTool,
} from './get-sample-data.js';

import {
  searchColumnsToolName,
  searchColumnsToolSchema,
  getSearchColumnsToolDefinition,
  executeSearchColumnsTool,
} from './search-columns.js';

import {
  explainQueryToolName,
  explainQueryToolSchema,
  getExplainQueryToolDefinition,
  executeExplainQueryTool,
} from './explain-query.js';

import {
  getRelationshipsToolName,
  getRelationshipsToolSchema,
  getGetRelationshipsToolDefinition,
  executeGetRelationshipsTool,
} from './get-relationships.js';

import {
  getTableStatsToolName,
  getTableStatsToolSchema,
  getGetTableStatsToolDefinition,
  executeGetTableStatsTool,
} from './get-table-stats.js';

import {
  validateQueryToolName,
  validateQueryToolSchema,
  getValidateQueryToolDefinition,
  executeValidateQueryTool,
} from './validate-query.js';

import {
  refreshSchemaToolName,
  refreshSchemaToolSchema,
  getRefreshSchemaToolDefinition,
  executeRefreshSchemaTool,
} from './refresh-schema.js';

import {
  getOntologyToolName,
  getOntologyToolSchema,
  getGetOntologyToolDefinition,
  executeGetOntologyTool,
} from './get-ontology.js';

// Re-export everything
export {
  queryToolName,
  queryToolSchema,
  getQueryToolDefinition,
  executeQueryTool,
  listTablesToolName,
  listTablesToolSchema,
  getListTablesToolDefinition,
  executeListTablesTool,
  listFunctionsToolName,
  listFunctionsToolSchema,
  getListFunctionsToolDefinition,
  executeListFunctionsTool,
  describeTableToolName,
  describeTableToolSchema,
  getDescribeTableToolDefinition,
  executeDescribeTableTool,
  schemaOverviewToolName,
  schemaOverviewToolSchema,
  getSchemaOverviewToolDefinition,
  executeSchemaOverviewTool,
  getSampleDataToolName,
  getSampleDataToolSchema,
  getGetSampleDataToolDefinition,
  executeGetSampleDataTool,
  searchColumnsToolName,
  searchColumnsToolSchema,
  getSearchColumnsToolDefinition,
  executeSearchColumnsTool,
  explainQueryToolName,
  explainQueryToolSchema,
  getExplainQueryToolDefinition,
  executeExplainQueryTool,
  getRelationshipsToolName,
  getRelationshipsToolSchema,
  getGetRelationshipsToolDefinition,
  executeGetRelationshipsTool,
  getTableStatsToolName,
  getTableStatsToolSchema,
  getGetTableStatsToolDefinition,
  executeGetTableStatsTool,
  validateQueryToolName,
  validateQueryToolSchema,
  getValidateQueryToolDefinition,
  executeValidateQueryTool,
  refreshSchemaToolName,
  refreshSchemaToolSchema,
  getRefreshSchemaToolDefinition,
  executeRefreshSchemaTool,
  getOntologyToolName,
  getOntologyToolSchema,
  getGetOntologyToolDefinition,
  executeGetOntologyTool,
};

/**
 * All tool definitions for registration with MCP server
 */
export function getAllToolDefinitions() {
  return [
    // Core query tools
    getQueryToolDefinition(),
    getExplainQueryToolDefinition(),
    getValidateQueryToolDefinition(),

    // Schema discovery tools
    getListTablesToolDefinition(),
    getListFunctionsToolDefinition(),
    getDescribeTableToolDefinition(),
    getSchemaOverviewToolDefinition(),
    getRefreshSchemaToolDefinition(),

    // Data exploration tools
    getGetSampleDataToolDefinition(),
    getSearchColumnsToolDefinition(),
    getGetRelationshipsToolDefinition(),
    getGetTableStatsToolDefinition(),

    // Semantic discovery tools
    getGetOntologyToolDefinition(),
  ];
}

/**
 * Tool name to executor mapping
 */
export const toolExecutors = {
  // Core query tools
  query: executeQueryTool,
  explain_query: executeExplainQueryTool,
  validate_query: executeValidateQueryTool,

  // Schema discovery tools
  list_tables: executeListTablesTool,
  list_functions: executeListFunctionsTool,
  describe_table: executeDescribeTableTool,
  schema_overview: executeSchemaOverviewTool,
  refresh_schema: executeRefreshSchemaTool,

  // Data exploration tools
  get_sample_data: executeGetSampleDataTool,
  search_columns: executeSearchColumnsTool,
  get_relationships: executeGetRelationshipsTool,
  get_table_stats: executeGetTableStatsTool,

  // Semantic discovery tools
  get_ontology: executeGetOntologyTool,
} as const;

export type ToolName = keyof typeof toolExecutors;

/**
 * Execute a tool by name
 */
export async function executeTool(
  name: string,
  args: Record<string, unknown>
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  const executor = toolExecutors[name as ToolName];

  if (!executor) {
    return {
      content: [
        {
          type: 'text',
          text: `Unknown tool: ${name}. Available tools: ${Object.keys(toolExecutors).join(', ')}`,
        },
      ],
    };
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return executor(args as any);
}
