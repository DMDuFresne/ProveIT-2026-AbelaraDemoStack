/**
 * Static descriptions for MES database entities
 * Provides rich context beyond database comments for AI assistants
 */

/**
 * MES domain terminology and concepts
 */
export const MES_CONCEPTS = `
## MES (Manufacturing Execution System) Concepts

### Core Entities
- **Asset**: Physical or logical equipment (machines, lines, cells, areas)
- **Product**: Items being manufactured, grouped into families
- **State**: Operational status of equipment (Running, Down, Idle, etc.)
- **Production Log**: Records of manufacturing runs with start/end times
- **Count Log**: Quantity tracking (infeed, outfeed, scrap)
- **Measurement Log**: Quality measurements with tolerance checking
- **KPI Log**: Calculated performance indicators over time windows

### Key Metrics
- **OEE (Overall Equipment Effectiveness)**: Availability × Performance × Quality
- **Availability**: (Run Time) / (Planned Production Time)
- **Performance**: (Actual Output) / (Theoretical Output)
- **Quality**: (Good Units) / (Total Units)

### State Types
- **Running**: Equipment is actively producing
- **Down**: Equipment is stopped (unplanned)
- **Idle**: Equipment is available but not producing
- **Changeover**: Transitioning between products
- **Maintenance**: Scheduled maintenance activity

### Data Patterns
- All log tables use soft-delete (removed=true) instead of hard delete
- Timestamps use TIMESTAMPTZ for timezone awareness
- Descriptive fields are snapshotted at log time for historical accuracy
- JSONB additional_info columns store flexible metadata
`;

/**
 * Schema overview with table relationships
 */
export const SCHEMA_OVERVIEW = `
## Database Schema Overview

### Schemas
- **mes_core**: Primary MES tables, views, and functions
- **mes_audit**: Change tracking and audit logs
- **mes_custom**: Customer-specific extensions

### Table Categories

#### Lookup Tables (Reference Data)
- \`asset_type\`: Categories of assets (Machine, Line, Cell, Area)
- \`state_type\`: State categories with downtime flags
- \`state_definition\`: Specific states mapped to types
- \`downtime_reason\`: Reasons for downtime (planned/unplanned)
- \`count_type\`: Types of counts (Good, Scrap, Rework)
- \`measurement_type\`: Types of measurements (Weight, Length, etc.)
- \`kpi_definition\`: KPI definitions with formulas

#### Master Data Tables
- \`asset_definition\`: Asset hierarchy with parent-child relationships
- \`product_family\`: Product groupings
- \`product_definition\`: Individual products with cycle times
- \`performance_target\`: Expected rates per asset/product combination

#### Log Tables (Time-Series Data)
- \`state_log\`: State transitions with timestamps
- \`production_log\`: Production runs with start/end times
- \`count_log\`: Quantity events tied to production runs
- \`measurement_log\`: Quality measurements with tolerances
- \`kpi_log\`: Calculated KPI values over time windows

#### Note Tables
- \`state_log_note\`, \`production_log_note\`, \`count_log_note\`, etc.
- Allow annotations on log entries

### Key Views
- \`vw_state_active\`: Current state per asset
- \`vw_state_timeline\`: State history with durations
- \`vw_state_downtime_events\`: Filtered downtime events
- \`vw_production_current\`: Active (open) production runs
- \`vw_production_yield\`: Yield calculations per run
- \`vw_production_throughput_rate\`: Performance vs ideal rate
- \`vw_kpi_latest\`: Most recent KPI per asset
- \`vw_unified_event_log\`: Combined event stream (use with filters!)

### Key Functions
- \`fn_get_asset_tree(root_id)\`: Get asset hierarchy
- \`fn_search_asset_ancestors(asset_id)\`: Find parent chain
- \`fn_search_asset_descendants(asset_id)\`: Find children
- \`fn_assets_without_state()\`: Find assets needing initialization
- \`fn_insert_*\`: Wrapper functions for inserting log records
`;

/**
 * Query examples for common use cases
 */
export const QUERY_EXAMPLES = `
## Query Examples

### Get Current State for All Assets
\`\`\`sql
SELECT * FROM mes_core.vw_state_active ORDER BY asset_name;
\`\`\`

### Get State History for an Asset (Last 24 Hours)
\`\`\`sql
SELECT * FROM mes_core.vw_state_timeline
WHERE asset_id = 1
  AND start_time >= NOW() - INTERVAL '24 hours'
ORDER BY start_time DESC;
\`\`\`

### Get Downtime Events with Reasons
\`\`\`sql
SELECT
  asset_name,
  state_name,
  downtime_reason_name,
  is_planned,
  start_time,
  duration_seconds / 60.0 as duration_minutes
FROM mes_core.vw_state_downtime_events
WHERE start_time >= NOW() - INTERVAL '7 days'
ORDER BY start_time DESC;
\`\`\`

### Get Active Production Runs
\`\`\`sql
SELECT * FROM mes_core.vw_production_current;
\`\`\`

### Calculate OEE Components for a Production Run
\`\`\`sql
-- Performance from throughput view
SELECT
  production_log_id,
  asset_name,
  product_name,
  performance_percent
FROM mes_core.vw_production_throughput_rate
WHERE production_log_id = 123;

-- Quality from yield view
SELECT
  production_log_id,
  yield_percent as quality_percent
FROM mes_core.vw_production_yield
WHERE production_log_id = 123;
\`\`\`

### Get Latest KPIs per Asset
\`\`\`sql
SELECT
  asset_name,
  kpi_name,
  kpi_value,
  start_ts,
  end_ts
FROM mes_core.vw_kpi_latest
ORDER BY asset_name, kpi_name;
\`\`\`

### Get Asset Hierarchy
\`\`\`sql
SELECT * FROM mes_core.fn_get_asset_tree(1, 10);
\`\`\`

### Find Assets with Data Quality Issues
\`\`\`sql
SELECT * FROM mes_core.vw_dq_assets_with_unknown_products;
\`\`\`

### Query Unified Event Log (ALWAYS filter by time!)
\`\`\`sql
SELECT * FROM mes_core.vw_unified_event_log
WHERE logged_at >= NOW() - INTERVAL '1 hour'
  AND asset_id = 1
ORDER BY logged_at DESC
LIMIT 100;
\`\`\`
`;

/**
 * Important warnings and best practices
 */
export const QUERY_WARNINGS = `
## Important Warnings

### Performance
- **vw_unified_event_log**: ALWAYS filter by \`logged_at\` and/or \`asset_id\` - this view queries 5 tables
- Log tables can be very large - always use time-based filters
- Use LIMIT to prevent returning excessive rows

### Data Integrity
- All tables use soft-delete: check \`removed IS DISTINCT FROM TRUE\` or \`removed = false\`
- Views already filter out removed records
- Production runs with \`end_ts IS NULL\` are still active

### Reserved IDs
- \`product_id = 1\` is reserved for "Unknown" product (data quality indicator)
- Check \`vw_dq_unknown_product_counts\` to monitor data quality
`;

/**
 * Complete tool description for the query tool
 */
export const QUERY_TOOL_DESCRIPTION = `Execute read-only SQL queries against the ProveIT MES database.

${MES_CONCEPTS}

${SCHEMA_OVERVIEW}

${QUERY_EXAMPLES}

${QUERY_WARNINGS}

## Security
- Only SELECT queries are allowed
- Queries run in READ ONLY transactions
- Statement timeout prevents long-running queries
- Results limited to prevent memory issues`;

/**
 * Table descriptions to supplement database comments
 */
export const TABLE_DESCRIPTIONS: Record<string, string> = {
  // Lookup tables
  'mes_core.asset_type':
    'Categories of manufacturing assets. Common types: Enterprise, Site, Area, Line, Cell, Machine.',
  'mes_core.state_type':
    'High-level state categories (Running, Down, Idle, etc.). The is_downtime flag determines if states count against availability.',
  'mes_core.state_definition':
    'Specific operational states mapped to state types. Each asset can be in one state at a time.',
  'mes_core.downtime_reason':
    'Reasons for equipment downtime. is_planned distinguishes scheduled maintenance from breakdowns.',
  'mes_core.count_type':
    'Types of quantity counts: Good (passed inspection), Scrap (rejected), Rework (needs rework).',
  'mes_core.measurement_type':
    'Quality measurement categories: Weight, Length, Temperature, Pressure, etc.',
  'mes_core.kpi_definition':
    'Key Performance Indicator definitions. kpi_formula documents the calculation methodology.',

  // Master data
  'mes_core.asset_definition':
    'Physical or logical manufacturing equipment. Supports hierarchical structure via parent_asset_id. tag_path links to Ignition SCADA tags.',
  'mes_core.product_family':
    'Groups related products for reporting. Example: "Beverage" family containing multiple SKUs.',
  'mes_core.product_definition':
    'Individual products/SKUs. ideal_cycle_time is target seconds per unit for performance calculations.',
  'mes_core.performance_target':
    'Expected production rates per asset+product combination. Used for calculating performance percentage.',

  // Log tables
  'mes_core.state_log':
    'Immutable state transition log. Each row represents entering a state. Durations calculated via views using LEAD().',
  'mes_core.production_log':
    'Production run records. end_ts=NULL indicates active run. Links count_log entries via production_log_id.',
  'mes_core.count_log':
    'Quantity events (parts produced). Links to production_log for context. product_id=1 indicates missing product data.',
  'mes_core.measurement_log':
    'Quality measurements with target/actual values. in_tolerance calculated from tolerance column.',
  'mes_core.kpi_log':
    'Pre-calculated KPI values over time windows. Avoids expensive real-time OEE calculations.',

  // Note tables
  'mes_core.state_log_note':
    'Operator notes attached to state transitions. Supports downtime annotations.',
  'mes_core.production_log_note':
    'Notes attached to production runs. Useful for shift handoff comments.',
  'mes_core.count_log_note': 'Notes explaining count adjustments or exceptions.',
  'mes_core.measurement_log_note':
    'Notes explaining measurement conditions or anomalies.',
  'mes_core.kpi_log_note': 'Notes explaining KPI variations or calculation context.',
  'mes_core.general_note':
    'Standalone notes not linked to specific events. Used for general shift notes.',

  // Key views
  'mes_core.vw_state_active':
    'Current (most recent) state per asset. Use for dashboards showing live equipment status.',
  'mes_core.vw_state_timeline':
    'State history with calculated durations. Shows start_time, end_time, duration_seconds for each state.',
  'mes_core.vw_state_downtime_events':
    'Filtered view of downtime events only. Includes is_planned from downtime_reason.',
  'mes_core.vw_state_duration_hourly':
    'Hourly aggregation of time spent in each state type per asset.',
  'mes_core.vw_state_duration_daily':
    'Daily aggregation of time spent in each state type per asset.',
  'mes_core.vw_production_log':
    'Production runs with aggregated count totals.',
  'mes_core.vw_production_current':
    'Active (open) production runs where end_ts IS NULL.',
  'mes_core.vw_production_yield':
    'Yield percentage per production run (good_quantity / total_quantity).',
  'mes_core.vw_production_throughput_rate':
    'Actual vs ideal rate, performance percentage per completed production run.',
  'mes_core.vw_production_state_summary':
    'Time spent in each state category during a production run.',
  'mes_core.vw_production_count_summary':
    'Count totals by type during production runs.',
  'mes_core.vw_production_measurement_summary':
    'Measurement statistics (avg, min, max) during production runs.',
  'mes_core.vw_measurement_summary_by_product':
    'Measurement statistics aggregated by product.',
  'mes_core.vw_measurement_out_of_tolerance':
    'Measurements that failed tolerance checks. Use for quality alerts.',
  'mes_core.vw_kpi_latest':
    'Most recent KPI value per asset and KPI definition.',
  'mes_core.vw_unified_event_log':
    'Combined view of all event types. WARNING: Always filter by logged_at to avoid full scans.',
  'mes_core.vw_dq_unknown_product_counts':
    'Data quality view showing counts with product_id=1 (Unknown).',
  'mes_core.vw_dq_unknown_product_summary_hourly':
    'Hourly summary of unknown product data quality issues.',
  'mes_core.vw_dq_unknown_product_summary_daily':
    'Daily summary with percentage of unknown product issues.',
  'mes_core.vw_dq_assets_with_unknown_products':
    'Assets that have logged counts against Unknown product. Check tag configuration.',
};

/**
 * Function descriptions to supplement database comments
 */
export const FUNCTION_DESCRIPTIONS: Record<string, string> = {
  'mes_core.fn_get_asset_tree':
    'Returns asset hierarchy starting from a root asset. Parameters: root_asset_id, max_level (default 10).',
  'mes_core.fn_search_asset_ancestors':
    'Finds all parent assets up to the enterprise level. Useful for rollup reporting.',
  'mes_core.fn_search_asset_descendants':
    'Finds all child assets under a parent. Useful for drilling down from area to machine.',
  'mes_core.fn_assets_without_state':
    'Returns assets that have never logged a state. Use to identify equipment needing initialization.',
  'mes_core.fn_insert_kpi_log':
    'Wrapper for inserting KPI records. Accepts additional_info as TEXT, converts to JSONB.',
  'mes_core.fn_insert_state_log':
    'Wrapper for inserting state transitions. Accepts additional_info as TEXT, converts to JSONB.',
  'mes_core.fn_insert_production_log':
    'Wrapper for inserting production runs. Accepts additional_info as TEXT, converts to JSONB.',
  'mes_core.fn_insert_count_log':
    'Wrapper for inserting count events. Accepts additional_info as TEXT, converts to JSONB.',
  'mes_core.fn_insert_measurement_log':
    'Wrapper for inserting measurements. Accepts additional_info as TEXT, converts to JSONB.',
};
