# MES Sample Data Structures

Example JSON structures returned by `mes.*` functions. Use these to understand data shapes for component development.

---

## Lookup Data

### lookups.getAssets()

```json
[
  {
    "asset_id": 1,
    "asset_name": "Line 1",
    "asset_description": "Primary Production Line",
    "asset_type_id": 2,
    "asset_type_name": "Line",
    "parent_asset_id": null,
    "tag_path": "Line1"
  },
  {
    "asset_id": 2,
    "asset_name": "Line 2",
    "asset_description": "Secondary Production Line",
    "asset_type_id": 2,
    "asset_type_name": "Line",
    "parent_asset_id": null,
    "tag_path": "Line2"
  }
]
```

### lookups.getStates()

```json
[
  {
    "state_id": 1,
    "state_name": "Running",
    "state_description": "Normal production",
    "state_type_id": 1,
    "state_type_name": "Operating",
    "state_color": "#4CAF50",
    "is_downtime": false
  },
  {
    "state_id": 2,
    "state_name": "Idle",
    "state_description": "Waiting for work",
    "state_type_id": 2,
    "state_type_name": "Idle",
    "state_color": "#2196F3",
    "is_downtime": false
  },
  {
    "state_id": 3,
    "state_name": "Down - Mechanical",
    "state_description": "Mechanical failure",
    "state_type_id": 3,
    "state_type_name": "Unplanned Stop",
    "state_color": "#F44336",
    "is_downtime": true
  }
]
```

### lookups.getProducts()

```json
[
  {
    "product_id": 1,
    "product_name": "Widget A",
    "product_description": "Standard Widget Model A",
    "product_family_id": 1,
    "product_family_name": "Widgets",
    "unit_of_measure": "each",
    "tolerance": 0.02,
    "ideal_cycle_time": 15.0
  },
  {
    "product_id": 2,
    "product_name": "Widget B",
    "product_description": "Premium Widget Model B",
    "product_family_id": 1,
    "product_family_name": "Widgets",
    "unit_of_measure": "each",
    "tolerance": 0.01,
    "ideal_cycle_time": 20.0
  }
]
```

### lookups.getDowntimeReasons()

```json
[
  {
    "downtime_reason_id": 1,
    "downtime_reason_code": "MECH01",
    "downtime_reason_name": "Mechanical Failure",
    "downtime_reason_description": "Equipment mechanical breakdown",
    "is_planned": false
  },
  {
    "downtime_reason_id": 2,
    "downtime_reason_code": "ELEC01",
    "downtime_reason_name": "Electrical Failure",
    "downtime_reason_description": "Electrical system malfunction",
    "is_planned": false
  },
  {
    "downtime_reason_id": 3,
    "downtime_reason_code": "PM01",
    "downtime_reason_name": "Preventive Maintenance",
    "downtime_reason_description": "Scheduled maintenance",
    "is_planned": true
  }
]
```

### lookups.getCountTypes()

```json
[
  {
    "count_type_id": 1,
    "count_type_name": "Good",
    "count_type_description": "Good/Finished parts",
    "count_type_unit": "each"
  },
  {
    "count_type_id": 2,
    "count_type_name": "Scrap",
    "count_type_description": "Defective parts",
    "count_type_unit": "each"
  },
  {
    "count_type_id": 3,
    "count_type_name": "Rework",
    "count_type_description": "Parts requiring rework",
    "count_type_unit": "each"
  }
]
```

### lookups.getMeasurementTypes()

```json
[
  {
    "measurement_type_id": 1,
    "measurement_type_name": "Weight",
    "measurement_type_description": "Part weight",
    "measurement_type_unit": "g"
  },
  {
    "measurement_type_id": 2,
    "measurement_type_name": "Length",
    "measurement_type_description": "Part length",
    "measurement_type_unit": "mm"
  }
]
```

---

## State Data

### state.getCurrentState(asset)

```json
{
  "asset_id": 1,
  "asset_name": "Line 1",
  "state_log_id": 456,
  "state_name": "Running",
  "state_type_name": "Operating",
  "is_downtime": false,
  "state_start": "2024-01-15T08:30:00",
  "downtime_reason_id": null,
  "downtime_reason_name": null,
  "additional_info": null,
  "logged_by": "system"
}
```

### state.getStateHistory(asset, hours=24)

```json
[
  {
    "state_log_id": 456,
    "asset_id": 1,
    "asset_name": "Line 1",
    "state_id": 1,
    "state_name": "Running",
    "state_type_id": 1,
    "state_type_name": "Operating",
    "is_downtime": false,
    "downtime_reason_id": null,
    "downtime_reason_code": null,
    "downtime_reason_name": null,
    "is_planned": null,
    "start_time": "2024-01-15T08:30:00",
    "end_time": null,
    "duration_seconds": 18000,
    "additional_info": null,
    "logged_by": "system"
  },
  {
    "state_log_id": 455,
    "asset_id": 1,
    "asset_name": "Line 1",
    "state_id": 3,
    "state_name": "Down - Mechanical",
    "state_type_id": 3,
    "state_type_name": "Unplanned Stop",
    "is_downtime": true,
    "downtime_reason_id": 1,
    "downtime_reason_code": "MECH01",
    "downtime_reason_name": "Mechanical Failure",
    "is_planned": false,
    "start_time": "2024-01-15T07:00:00",
    "end_time": "2024-01-15T08:30:00",
    "duration_seconds": 5400,
    "additional_info": {"technician": "John Smith"},
    "logged_by": "operator"
  }
]
```

### state.getDowntimeSummary(asset, hours=168)

```json
[
  {
    "downtime_reason_code": "MECH01",
    "downtime_reason_name": "Mechanical Failure",
    "is_planned": false,
    "event_count": 5,
    "total_duration_seconds": 16200
  },
  {
    "downtime_reason_code": "ELEC01",
    "downtime_reason_name": "Electrical Failure",
    "is_planned": false,
    "event_count": 2,
    "total_duration_seconds": 7200
  },
  {
    "downtime_reason_code": "MAT01",
    "downtime_reason_name": "Material Shortage",
    "is_planned": false,
    "event_count": 3,
    "total_duration_seconds": 5400
  }
]
```

### state.getStateDurationSummary(asset, hours=24)

```json
[
  {
    "state_type_name": "Operating",
    "total_duration_seconds": 64800
  },
  {
    "state_type_name": "Unplanned Stop",
    "total_duration_seconds": 10800
  },
  {
    "state_type_name": "Idle",
    "total_duration_seconds": 7200
  },
  {
    "state_type_name": "Planned Stop",
    "total_duration_seconds": 3600
  }
]
```

---

## Production Data

### production.getActiveRun(asset)

```json
{
  "production_log_id": 123,
  "asset_id": 1,
  "asset_name": "Line 1",
  "product_id": 1,
  "product_name": "Widget A",
  "start_ts": "2024-01-15T06:00:00",
  "total_count": 1250,
  "additional_info": {"workOrder": "WO-2024-001", "lotNumber": "LOT-ABC"},
  "logged_by": "operator",
  "logged_at": "2024-01-15T06:00:00"
}
```

**Returns `null` if no active run.**

### production.getRunHistory(asset, hours=24)

```json
[
  {
    "production_log_id": 123,
    "asset_id": 1,
    "asset_name": "Line 1",
    "product_id": 1,
    "product_name": "Widget A",
    "start_ts": "2024-01-15T06:00:00",
    "end_ts": null,
    "total_count": 1250,
    "additional_info": {"workOrder": "WO-2024-001"},
    "logged_by": "operator",
    "logged_at": "2024-01-15T06:00:00",
    "removed": false
  },
  {
    "production_log_id": 122,
    "asset_id": 1,
    "asset_name": "Line 1",
    "product_id": 2,
    "product_name": "Widget B",
    "start_ts": "2024-01-14T14:00:00",
    "end_ts": "2024-01-14T22:00:00",
    "total_count": 800,
    "additional_info": {"workOrder": "WO-2024-000"},
    "logged_by": "operator",
    "logged_at": "2024-01-14T14:00:00",
    "removed": false
  }
]
```

### production.getRunYield(productionLogId)

```json
{
  "production_log_id": 123,
  "asset_id": 1,
  "asset_name": "Line 1",
  "product_id": 1,
  "product_name": "Widget A",
  "good_quantity": 1200,
  "total_quantity": 1250,
  "yield_percent": 96.0
}
```

### production.getRunThroughput(productionLogId)

```json
{
  "production_log_id": 123,
  "asset_id": 1,
  "asset_name": "Line 1",
  "product_id": 1,
  "product_name": "Widget A",
  "ideal_cycle_time": 15.0,
  "start_ts": "2024-01-15T06:00:00",
  "end_ts": "2024-01-15T14:00:00",
  "run_duration_seconds": 28800,
  "total_count": 1250,
  "actual_rate": 0.0434,
  "ideal_rate": 0.0667,
  "performance_percent": 65.1
}
```

---

## Count Data

### counts.getCountHistory(asset, hours=24)

```json
[
  {
    "count_log_id": 789,
    "asset_id": 1,
    "asset_name": "Line 1",
    "production_log_id": 123,
    "count_type_id": 1,
    "count_type_name": "Good",
    "quantity": 100,
    "product_id": 1,
    "product_name": "Widget A",
    "product_family_id": 1,
    "product_family_name": "Widgets",
    "additional_info": null,
    "logged_by": "plc",
    "logged_at": "2024-01-15T12:00:00"
  },
  {
    "count_log_id": 788,
    "asset_id": 1,
    "asset_name": "Line 1",
    "production_log_id": 123,
    "count_type_id": 2,
    "count_type_name": "Scrap",
    "quantity": 5,
    "product_id": 1,
    "product_name": "Widget A",
    "product_family_id": 1,
    "product_family_name": "Widgets",
    "additional_info": {"reason": "Dimensional"},
    "logged_by": "operator",
    "logged_at": "2024-01-15T11:30:00"
  }
]
```

### counts.getCountSummary(asset, hours=24)

```json
[
  {
    "count_type_id": 1,
    "count_type_name": "Good",
    "total_quantity": 1200,
    "count_events": 24
  },
  {
    "count_type_id": 2,
    "count_type_name": "Scrap",
    "total_quantity": 45,
    "count_events": 8
  },
  {
    "count_type_id": 3,
    "count_type_name": "Rework",
    "total_quantity": 15,
    "count_events": 3
  }
]
```

### counts.getYield(asset, hours=24)

```json
{
  "good_count": 1200,
  "total_count": 1260,
  "yield_percent": 95.24
}
```

---

## Quality Data

### quality.getMeasurementHistory(asset, hours=24)

```json
[
  {
    "measurement_log_id": 501,
    "asset_id": 1,
    "asset_name": "Line 1",
    "product_id": 1,
    "product_name": "Widget A",
    "product_family_id": 1,
    "product_family_name": "Widgets",
    "measurement_type_id": 1,
    "measurement_type_name": "Weight",
    "target_value": 100.0,
    "actual_value": 100.5,
    "unit_of_measure": "g",
    "tolerance": 0.02,
    "in_tolerance": true,
    "additional_info": null,
    "logged_by": "sensor",
    "logged_at": "2024-01-15T12:15:00"
  },
  {
    "measurement_log_id": 500,
    "asset_id": 1,
    "asset_name": "Line 1",
    "product_id": 1,
    "product_name": "Widget A",
    "product_family_id": 1,
    "product_family_name": "Widgets",
    "measurement_type_id": 1,
    "measurement_type_name": "Weight",
    "target_value": 100.0,
    "actual_value": 105.0,
    "unit_of_measure": "g",
    "tolerance": 0.02,
    "in_tolerance": false,
    "additional_info": null,
    "logged_by": "sensor",
    "logged_at": "2024-01-15T12:00:00"
  }
]
```

### quality.getOutOfSpecMeasurements(asset, hours=24)

```json
[
  {
    "measurement_log_id": 500,
    "asset_id": 1,
    "asset_name": "Line 1",
    "product_id": 1,
    "product_name": "Widget A",
    "measurement_type_id": 1,
    "measurement_type_name": "Weight",
    "unit_of_measure": "g",
    "target_value": 100.0,
    "actual_value": 105.0,
    "tolerance": 0.02,
    "in_tolerance": false,
    "logged_by": "sensor",
    "logged_at": "2024-01-15T12:00:00",
    "additional_info": null
  }
]
```

### quality.getMeasurementSummary(asset, hours=24)

```json
[
  {
    "measurement_type_id": 1,
    "measurement_type_name": "Weight",
    "unit_of_measure": "g",
    "sample_count": 150,
    "avg_value": 100.2,
    "min_value": 98.5,
    "max_value": 105.0,
    "in_tolerance_count": 145,
    "out_of_tolerance_count": 5
  },
  {
    "measurement_type_id": 2,
    "measurement_type_name": "Length",
    "unit_of_measure": "mm",
    "sample_count": 75,
    "avg_value": 150.1,
    "min_value": 149.0,
    "max_value": 151.5,
    "in_tolerance_count": 74,
    "out_of_tolerance_count": 1
  }
]
```

### quality.getFirstPassYield(asset, hours=24)

```json
{
  "in_tolerance_count": 219,
  "total_count": 225,
  "first_pass_yield": 97.33
}
```

---

## KPI Data

### kpi.getLatestKPI(asset, kpiName)

```json
{
  "asset_id": 1,
  "asset_name": "Line 1",
  "kpi_id": 1,
  "kpi_name": "Yield",
  "kpi_value": 95.24,
  "start_ts": "2024-01-15T06:00:00",
  "end_ts": "2024-01-15T14:00:00",
  "logged_at": "2024-01-15T14:00:00",
  "logged_by": "system"
}
```

### kpi.getKPITrend(asset, kpiName, days=7)

```json
[
  {
    "end_ts": "2024-01-09T14:00:00",
    "kpi_value": 92.5,
    "additional_info": null
  },
  {
    "end_ts": "2024-01-10T14:00:00",
    "kpi_value": 94.2,
    "additional_info": null
  },
  {
    "end_ts": "2024-01-11T14:00:00",
    "kpi_value": 93.8,
    "additional_info": null
  },
  {
    "end_ts": "2024-01-12T14:00:00",
    "kpi_value": 95.1,
    "additional_info": null
  },
  {
    "end_ts": "2024-01-13T14:00:00",
    "kpi_value": 94.5,
    "additional_info": null
  },
  {
    "end_ts": "2024-01-14T14:00:00",
    "kpi_value": 96.0,
    "additional_info": null
  },
  {
    "end_ts": "2024-01-15T14:00:00",
    "kpi_value": 95.24,
    "additional_info": null
  }
]
```

### kpi.getKPIAverage(asset, kpiName, days=7)

```json
{
  "avg_value": 94.47,
  "min_value": 92.5,
  "max_value": 96.0,
  "sample_count": 7
}
```

---

## Embr Chart Data Formats

### Pareto Chart (ApexCharts Bar)

Transform `state.getDowntimeSummary()` to:

```json
{
  "type": "bar",
  "options": {
    "chart": {"id": "downtime-pareto"},
    "plotOptions": {"bar": {"horizontal": true}},
    "xaxis": {
      "categories": ["Mechanical Failure", "Electrical Failure", "Material Shortage"]
    },
    "colors": ["#F44336"]
  },
  "series": [{
    "name": "Hours",
    "data": [4.5, 2.0, 1.5]
  }]
}
```

### Time Series (ApexCharts Line)

Transform `kpi.getKPITrend()` to:

```json
{
  "type": "line",
  "options": {
    "chart": {"id": "yield-trend", "zoom": {"enabled": true}},
    "xaxis": {"type": "datetime"},
    "yaxis": {"min": 0, "max": 100}
  },
  "series": [{
    "name": "Yield",
    "data": [
      ["2024-01-09T14:00:00", 92.5],
      ["2024-01-10T14:00:00", 94.2],
      ["2024-01-11T14:00:00", 93.8],
      ["2024-01-12T14:00:00", 95.1],
      ["2024-01-13T14:00:00", 94.5],
      ["2024-01-14T14:00:00", 96.0],
      ["2024-01-15T14:00:00", 95.24]
    ]
  }]
}
```

### Donut Chart (ApexCharts)

Transform `state.getStateDurationSummary()` to:

```json
{
  "type": "donut",
  "options": {
    "chart": {"id": "state-distribution"},
    "labels": ["Operating", "Unplanned Stop", "Idle", "Planned Stop"],
    "colors": ["#4CAF50", "#F44336", "#2196F3", "#9C27B0"]
  },
  "series": [64800, 10800, 7200, 3600]
}
```

### Gauge (ApexCharts RadialBar)

```json
{
  "type": "radialBar",
  "options": {
    "chart": {"id": "yield-gauge"},
    "plotOptions": {
      "radialBar": {
        "startAngle": -135,
        "endAngle": 135,
        "dataLabels": {
          "name": {"show": true},
          "value": {"formatter": "function(val) { return val + '%' }"}
        }
      }
    },
    "labels": ["Yield"]
  },
  "series": [95.24]
}
```
