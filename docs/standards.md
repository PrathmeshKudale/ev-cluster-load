# Open Standards Compliance: OCPP 1.6J & OSCP 2.0

This document outlines the implemented open standards subset in **EV Cluster Load**, providing interoperability with physical/simulated EV chargers and distribution grid operators (DSOs).

---

## 1. OCPP 1.6J (Open Charge Point Protocol JSON)

The Central System exposes a standards-compliant WebSocket endpoint supporting the `ocpp1.6` subprotocol.

### 1.1 Central System Endpoint

- **URI**: `ws://<host>:<port>/ocpp/{charger_id}` (also mounted at `/api/v1/ocpp/{charger_id}`)
- **Subprotocol**: `ocpp1.6`
- **Framing**: JSON-RPC 2.0 arrays:
  - **Call (Client -> Central System)**: `[2, "<unique_id>", "<action>", { <payload> }]`
  - **CallResult (Central System -> Client)**: `[3, "<unique_id>", { <payload> }]`
  - **CallError**: `[4, "<unique_id>", "<errorCode>", "<errorDescription>", {}]`

### 1.2 Implemented Core Profile Actions

| OCPP Action | Direction | Purpose | Central System Response |
| :--- | :--- | :--- | :--- |
| `BootNotification` | ChargePoint -> CS | Charger startup registration and handshake | `{"status": "Accepted", "currentTime": "<ISO8601>", "interval": 30}` |
| `StatusNotification` | ChargePoint -> CS | Inform status transitions (`Available`, `Occupied`, `Charging`, `Faulted`) | `{}` |
| `StartTransaction` | ChargePoint -> CS | Driver authorizes and begins active charging | `{"transactionId": <int>, "idTagInfo": {"status": "Accepted"}}` |
| `MeterValues` | ChargePoint -> CS | Periodic telemetry for active power (`kW`) and energy registers (`Wh`) | `{}` |
| `StopTransaction` | ChargePoint -> CS | Session termination, final energy reading, and disconnect | `{"idTagInfo": {"status": "Accepted"}}` |

### 1.3 Mock Charger Client

A complete mock charger client using the official Python `ocpp` library is provided in:
- Module: `app.services.mock_charger.MockChargerClient`
- High-level test helper: `app.services.mock_charger.run_mock_charging_session`
- Command-line runner: `scripts/mock_charger.py`

#### CLI Usage:
```bash
python scripts/mock_charger.py --url ws://localhost:8000/ocpp/CP-101 --charger-id CP-101 --energy-kwh 14.8
```

---

## 2. OSCP 2.0 (Open Smart Charging Protocol)

The Open Smart Charging Protocol enables communication between the Distribution System Operator (DSO) and the Charging Station Operator (CSO) to balance grid capacity and avoid substation overloads.

### 2.1 Dynamic Capacity Forecast Endpoint

- **Method**: `PUT`
- **Path**: `/oscp/capacity-forecast` (also available at `/api/v1/oscp/capacity-forecast`)
- **Headers**: `Content-Type: application/json`

#### Request Payload:
```json
{
  "max_capacity_kva": 65.0,
  "forecast_hours": [65.0, 65.0, 60.0, 55.0, 50.0, ...],
  "reason": "DSO 11kV feeder scheduled maintenance"
}
```

#### Response:
```json
{
  "status": "Accepted",
  "applied_capacity_kva": 65.0,
  "current_load_kva": 52.6,
  "alert_triggered": false,
  "forecast_hours": [...],
  "reason": "DSO 11kV feeder scheduled maintenance",
  "timestamp": "2026-10-13T04:45:00.000Z"
}
```

### 2.2 Instantaneous Overload Protection (Within 1 Tick)

When an external DSO pushes an updated capacity limit:
1. `OcppService` compares the new `max_capacity_kva` against the active cluster load:
   $$\text{Current Load (kVA)} = \frac{\text{Baseline Load (kW)} + \sum \text{Active Charger Power (kW)}}{\text{Power Factor (0.95)}}$$
2. If the limit drops below the active load ($\text{limit} < \text{current\_load}$):
   - An immediate high-priority alert (`ALT-OSCP-*`) is generated within the current tick:
     `"DSO OSCP capacity limit (60.0 kVA) dropped below current load (65.2 kVA)! Overload risk."`
   - Transformer risk status transitions immediately from `ok`/`warning` to `critical`.
   - Replay frames, live telemetry, and `/api/v1/transformer/T1/risk` reflect the increased relative loading percentage and alert state.

---

## 3. Session and Charger Visibility

The system exposes REST endpoints to monitor live OCPP transactions and connected chargers:

- **`GET /sessions`** (or `/api/v1/sessions`):
  Lists active and completed charging sessions with start/stop times, energy delivered (kWh), and termination reason.
- **`GET /standards/chargers`** (or `/api/v1/standards/chargers`):
  Lists online charge points, firmware versions, and real-time kW output.
- **`GET /standards/alerts`** (or `/api/v1/standards/alerts`):
  Lists active grid overload alerts triggered by OSCP capacity changes.

---

## 4. Verification and Automated Testing

All standards functionality is covered by automated unit and integration tests:

```bash
# Run standards test suite
pytest backend/tests/test_standards.py -v
```

The test suite validates:
1. Full 5-message OCPP 1.6J lifecycle over WebSocket using `MockChargerClient`.
2. Session appearance in session summaries and database persistence layer.
3. Lowering OSCP capacity limit triggers an immediate overload alert within one tick.
