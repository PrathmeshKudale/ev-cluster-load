# EV Cluster Load Database Schema

This document details the relational entity relationships and hypertable structure across the three architectural schemas: `raw`, `clean`, and `features`.

## Entity-Relationship Diagram

```mermaid
erDiagram
    %% Clean Schema Core Entities
    CLUSTERS ||--o{ TRANSFORMERS : "powers"
    CLUSTERS ||--o{ STATIONS : "contains"
    TRANSFORMERS ||--o{ STATIONS : "supplies"
    TRANSFORMERS ||--|| CONFIG_TRANSFORMER : "configured by"
    TRANSFORMERS ||--o{ CONFIG_DERATING_CURVE : "derated by"
    TRANSFORMERS ||--o{ TRANSFORMER_RISK : "monitored in"
    STATIONS ||--o{ CHARGERS : "hosts"
    CHARGERS ||--o{ SESSIONS : "delivers"
    STATIONS ||--o{ SESSIONS : "locates"
    STATIONS ||--o{ STATION_LOAD : "aggregated into"
    CLUSTERS ||--o{ WEATHER : "experiences"
    STATIONS ||--o{ FORECASTS : "predicts"
    STATIONS ||--o{ RECOMMENDATIONS : "suggested in"
    SIM_RUNS ||--o{ SIM_METRICS : "produces"

    %% Features Schema
    STATIONS ||--o{ STATION_EDGES : "src / dst node"
    STATIONS ||--o{ HOURLY_CLUSTER_FEATURES : "featurized for GNN"

    CLUSTERS {
        string id PK
        string name
        string description
        timestamptz created_at
        timestamptz updated_at
    }

    TRANSFORMERS {
        string id PK
        string cluster_id FK
        string name
        float rating_kva
        float power_factor
        float warn_threshold_pct
        float crit_threshold_pct
        timestamptz created_at
        timestamptz updated_at
    }

    STATIONS {
        string id PK
        string cluster_id FK
        string transformer_id FK
        string name
        geometry geom "Point EPSG:4326"
        float latitude
        float longitude
        float detour_min
        boolean is_synthetic
        timestamptz created_at
        timestamptz updated_at
    }

    CHARGERS {
        string id PK
        string station_id FK
        int evse_id
        float max_kw
        string connector_type
        string status
        timestamptz created_at
        timestamptz updated_at
    }

    SESSIONS {
        string id PK
        timestamptz start_time PK "Hypertable Dim"
        string charger_id FK
        string station_id FK
        string user_hash "SHA-256 no PII"
        timestamptz end_time
        float energy_kwh
        float peak_kw
        boolean is_synthetic
        timestamptz created_at
    }

    STATION_LOAD {
        string station_id PK, FK
        timestamptz timestamp PK "Hypertable Dim"
        float active_kw
        int active_chargers
        float utilization_rate
    }

    WEATHER {
        string cluster_id PK, FK
        timestamptz timestamp PK "Hypertable Dim"
        float temperature_c
        float precipitation_mm
        float wind_speed_ms
        float solar_irradiance
    }

    FORECASTS {
        string station_id PK, FK
        timestamptz issued_at PK
        timestamptz target_ts PK "Hypertable Dim"
        float p10
        float p50
        float p90
        string model_version
    }

    TRANSFORMER_RISK {
        string id PK
        string transformer_id FK
        timestamptz timestamp
        float forecast_p90_pct
        string risk_level
        boolean alert_raised
        timestamptz created_at
    }

    RECOMMENDATIONS {
        string id PK
        string session_request_id
        string user_hash
        string mode
        string recommended_station_id FK
        timestamptz recommended_slot_start
        int rank
        float score
        float expected_wait_min
        float expected_detour_min
        float grid_load_pct
        timestamptz created_at
    }

    CONFIG_TRANSFORMER {
        string transformer_id PK, FK
        float nominal_kva
        float power_factor
        float warn_threshold_pct
        float crit_threshold_pct
        string cooling_class
        float ambient_ref_temp_c
        timestamptz created_at
        timestamptz updated_at
    }

    CONFIG_DERATING_CURVE {
        int id PK
        string transformer_id FK
        float ambient_temp_c
        float derating_factor
        string description
    }

    CONFIG_TOD_TARIFF {
        int id PK
        string name
        int start_hour
        int end_hour
        float rate_inr_per_kwh
        float peak_multiplier
        string description
    }

    STATION_EDGES {
        string src_station_id PK, FK
        string dst_station_id PK, FK
        float distance_km
        float drive_minutes
        string source_method
        float weight
        timestamptz updated_at
    }

    HOURLY_CLUSTER_FEATURES {
        string station_id PK, FK
        timestamptz timestamp PK
        int hour_of_day
        int day_of_week
        boolean is_weekend
        float active_kw
        float lag_load_1h
        float lag_load_24h
        float temp_c
        float tod_tariff_multiplier
    }

    USERS {
        string user_hash PK "SHA-256 no PII"
        text preferences_json
        timestamptz created_at
    }

    AUDIT_LOG {
        bigint id PK
        string action
        string entity_type
        string entity_id
        text details
        timestamptz created_at
    }
```

## TimescaleDB Hypertables
The following tables are partitioned by time to support high-throughput ingestion and sub-second analytical queries:
1. `clean.sessions` (partitioned on `start_time`)
2. `clean.station_load` (partitioned on `timestamp`)
3. `clean.weather` (partitioned on `timestamp`)
4. `clean.forecasts` (partitioned on `target_ts`)
