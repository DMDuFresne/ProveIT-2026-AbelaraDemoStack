# Entity Relationship Diagrams

This document provides visual entity relationship diagrams for all MES database schemas using Mermaid syntax.

---

## Schema Overview

```mermaid
erDiagram
    MES_CORE ||--o{ MES_AUDIT : "audits"
    MES_CORE ||--o{ MES_CUSTOM : "extends"

    MES_CORE {
        string Lookup_Tables
        string Master_Data
        string Log_Tables
        string Views
    }

    MES_AUDIT {
        string change_log
    }

    MES_CUSTOM {
        string state_xref
        string item_xref
    }
```

---

## mes_core: Lookup Tables

```mermaid
erDiagram
    asset_type {
        bigint asset_type_id PK
        text asset_type_name UK
        text asset_type_description
        boolean removed
    }

    state_type {
        bigint state_type_id PK
        text state_type_name UK
        text state_type_color
        boolean is_downtime
        boolean removed
    }

    state_definition {
        bigint state_id PK
        bigint state_type_id FK
        text state_name UK
        text state_color
        boolean removed
    }

    downtime_reason {
        bigint downtime_reason_id PK
        text downtime_reason_code UK
        text downtime_reason_name
        boolean is_planned
        boolean removed
    }

    count_type {
        bigint count_type_id PK
        text count_type_name
        text count_type_unit
        boolean removed
    }

    measurement_type {
        bigint measurement_type_id PK
        text measurement_type_name
        text measurement_type_unit
        boolean removed
    }

    kpi_definition {
        bigint kpi_id PK
        text kpi_name UK
        text kpi_unit
        text kpi_formula
        boolean removed
    }

    state_type ||--o{ state_definition : "categorizes"
```

---

## mes_core: Master Data Tables

```mermaid
erDiagram
    asset_type ||--o{ asset_definition : "types"
    asset_definition ||--o{ asset_definition : "parent"
    product_family ||--o{ product_definition : "groups"
    asset_definition ||--o{ performance_target : "targets"
    product_definition ||--o{ performance_target : "targets"

    asset_definition {
        bigint asset_id PK
        text asset_name
        text asset_description
        bigint asset_type_id FK
        bigint parent_asset_id FK
        text tag_path
        boolean removed
    }

    product_family {
        bigint product_family_id PK
        text product_family_name UK
        text product_family_description
        boolean removed
    }

    product_definition {
        bigint product_id PK
        text product_name
        text product_description
        bigint product_family_id FK
        text unit_of_measure
        numeric tolerance
        numeric ideal_cycle_time
        boolean removed
    }

    performance_target {
        bigint performance_target_id PK
        bigint product_id FK
        bigint asset_id FK
        numeric target_value
        text target_unit
        boolean removed
    }
```

---

## mes_core: Log Tables (Hypertables)

```mermaid
erDiagram
    asset_definition ||--o{ state_log : "logs"
    state_definition ||--o{ state_log : "states"
    state_type ||--o{ state_log : "types"
    downtime_reason ||--o{ state_log : "reasons"
    state_log ||--o{ state_log_note : "notes"

    asset_definition ||--o{ production_log : "produces"
    product_definition ||--o{ production_log : "products"
    product_family ||--o{ production_log : "families"
    production_log ||--o{ production_log_note : "notes"
    production_log ||--o{ count_log : "counts"

    asset_definition ||--o{ count_log : "logs"
    count_type ||--o{ count_log : "types"
    product_definition ||--o{ count_log : "products"
    product_family ||--o{ count_log : "families"
    count_log ||--o{ count_log_note : "notes"

    asset_definition ||--o{ measurement_log : "measures"
    measurement_type ||--o{ measurement_log : "types"
    product_definition ||--o{ measurement_log : "products"
    product_family ||--o{ measurement_log : "families"
    measurement_log ||--o{ measurement_log_note : "notes"

    asset_definition ||--o{ kpi_log : "kpis"
    kpi_definition ||--o{ kpi_log : "definitions"
    kpi_log ||--o{ kpi_log_note : "notes"

    state_log {
        bigint state_log_id
        bigint asset_id FK
        text asset_name
        bigint state_id FK
        text state_name
        bigint state_type_id FK
        text state_type_name
        bigint from_state_id
        bigint downtime_reason_id FK
        timestamptz logged_at PK
        boolean removed
    }

    production_log {
        bigint production_log_id
        bigint asset_id FK
        text asset_name
        bigint product_id FK
        text product_name
        bigint product_family_id FK
        timestamptz start_ts
        timestamptz end_ts
        timestamptz logged_at PK
        boolean removed
    }

    count_log {
        bigint count_log_id
        bigint asset_id FK
        bigint production_log_id FK
        bigint count_type_id FK
        numeric quantity
        bigint product_id FK
        bigint product_family_id FK
        timestamptz logged_at PK
        boolean removed
    }

    measurement_log {
        bigint measurement_log_id
        bigint asset_id FK
        bigint product_id FK
        bigint measurement_type_id FK
        numeric target_value
        numeric actual_value
        boolean in_tolerance
        timestamptz logged_at PK
        boolean removed
    }

    kpi_log {
        bigint kpi_log_id
        bigint asset_id FK
        bigint kpi_id FK
        numeric kpi_value
        timestamptz start_ts
        timestamptz end_ts
        timestamptz logged_at PK
        boolean removed
    }

    state_log_note {
        bigint note_id PK
        bigint state_log_id FK
        text note
        boolean removed
    }

    production_log_note {
        bigint note_id PK
        bigint production_log_id FK
        text note
        boolean removed
    }

    count_log_note {
        bigint note_id PK
        bigint count_log_id FK
        text note
        boolean removed
    }

    measurement_log_note {
        bigint note_id PK
        bigint measurement_log_id FK
        text note
        boolean removed
    }

    kpi_log_note {
        bigint note_id PK
        bigint kpi_log_id FK
        text note
        boolean removed
    }
```

---

## mes_custom: Pilot Integration

```mermaid
erDiagram
    state_definition ||--o{ state_xref : "maps to"
    product_definition ||--o{ item_xref : "maps to"
    item_xref ||--o{ item_extended_attributes : "extends"
    item_xref ||--o{ item_extended_attributes : "parent BOM"

    state_xref {
        int pilot_state_code PK
        varchar pilot_state_name
        varchar pilot_state_type
        bigint mes_state_id FK
        text notes
    }

    item_xref {
        bigint pilot_item_id PK
        varchar pilot_item_name
        bigint mes_product_id FK
    }

    item_extended_attributes {
        bigint pilot_item_id PK_FK
        bigint parent_item_id FK
        varchar item_class
        varchar bottle_size
        varchar label_variant
        int pack_count
    }
```

---

## mes_audit: Change Log

```mermaid
erDiagram
    change_log {
        bigint audit_id PK
        text schema_name
        text table_name
        text operation
        text record_key
        text record_value
        jsonb column_changes
        text changed_by
        timestamptz changed_at
    }
```

---

## Asset Hierarchy Example

```mermaid
graph TD
    A[Plant: Abelara] --> B[Area: Mixing]
    A --> C[Area: Filling]
    A --> D[Area: Packaging]
    A --> E[Area: Palletizing]

    B --> B1[Tank1]
    B --> B2[Tank2]
    B --> B3[Vat1]

    C --> C1[Line1]
    C --> C2[Line2]

    C1 --> C1a[Filler1]
    C1 --> C1b[Capper1]
    C1 --> C1c[Labeler1]

    D --> D1[Packager1]
    D --> D2[Sealer1]

    E --> E1[Robot1]
    E --> E2[PalletStation1]
```

---

## Data Flow: State to KPI

```mermaid
sequenceDiagram
    participant PLC
    participant Tags
    participant StateLog
    participant KPICalc
    participant KPILog

    PLC->>Tags: State Change
    Tags->>StateLog: logState()
    Note over StateLog: Trigger populates descriptives

    loop Every Hour (CRON)
        KPICalc->>StateLog: Query vw_state_timeline
        KPICalc->>KPICalc: Calculate A, P, Q, OEE
        KPICalc->>Tags: Write to KPI/Value
        Tags->>KPILog: LogTrigger fires
    end
```

---

## Production Data Flow

```mermaid
sequenceDiagram
    participant Operator
    participant Tags
    participant ProdLog
    participant CountLog
    participant MeasLog

    Operator->>Tags: Start Production
    Tags->>ProdLog: startProductionRun()
    Note over ProdLog: Auto-populate names

    loop During Production
        Tags->>CountLog: recordCount(Good)
        Tags->>CountLog: recordCount(Scrap)
        Tags->>MeasLog: recordMeasurement(Weight)
    end

    Operator->>Tags: End Production
    Tags->>ProdLog: endProductionRun()
```

---

## Related Documentation

- [Schema Reference](../05-Database/schema-reference.md) - Table details
- [Custom Schema Reference](../05-Database/custom-schema-reference.md) - Pilot integration
- [Views Reference](../05-Database/views-reference.md) - View documentation
- [Architecture Overview](../01-Overview/architecture.md) - System design
