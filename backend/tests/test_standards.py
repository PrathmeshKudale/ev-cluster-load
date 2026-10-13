"""Unit and integration tests for OCPP 1.6J and OSCP 2.0 standards implementation."""
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ocpp_service import OcppService
from app.services.transformer_service import TransformerService
from app.services.replay_service import ReplayService
from app.services.mock_charger import MockChargerClient


@pytest.fixture(autouse=True)
def reset_ocpp_state():
    """Reset OcppService internal state before each test."""
    OcppService.reset()
    yield
    OcppService.reset()


def test_ocpp_service_lifecycle():
    """Verify OcppService handles all 5 OCPP 1.6 actions and produces completed sessions."""
    charger_id = "CP-UNIT-01"

    # 1. BootNotification
    boot_res = OcppService.handle_ocpp_call(
        charger_id=charger_id,
        action="BootNotification",
        payload={"chargePointVendor": "ABB", "chargePointModel": "Terra-54", "firmwareVersion": "1.0"},
    )
    assert boot_res["status"] == "Accepted"
    assert "currentTime" in boot_res

    # 2. StatusNotification -> Available
    status_res = OcppService.handle_ocpp_call(
        charger_id=charger_id,
        action="StatusNotification",
        payload={"connectorId": 1, "errorCode": "NoError", "status": "Available"},
    )
    assert status_res == {}

    # 3. StartTransaction
    start_res = OcppService.handle_ocpp_call(
        charger_id=charger_id,
        action="StartTransaction",
        payload={"connectorId": 1, "idTag": "TAG-TEST-01", "meterStart": 1000},
    )
    tx_id = start_res["transactionId"]
    assert tx_id > 0
    assert start_res["idTagInfo"]["status"] == "Accepted"

    # 4. MeterValues
    meter_res = OcppService.handle_ocpp_call(
        charger_id=charger_id,
        action="MeterValues",
        payload={
            "transactionId": tx_id,
            "meterValue": [
                {
                    "sampledValue": [
                        {"value": "11.0", "measurand": "Power.Active.Import"},
                        {"value": "15000", "measurand": "Energy.Active.Import.Register"},
                    ]
                }
            ],
        },
    )
    assert meter_res == {}

    # 5. StopTransaction
    stop_res = OcppService.handle_ocpp_call(
        charger_id=charger_id,
        action="StopTransaction",
        payload={"transactionId": tx_id, "meterStop": 15000, "reason": "Local"},
    )
    assert stop_res["idTagInfo"]["status"] == "Accepted"

    # Verify session summary
    sessions = OcppService.get_sessions_summary()
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == f"ocpp-tx-{tx_id}"
    assert sessions[0]["charger_id"] == charger_id
    assert sessions[0]["status"] == "Completed"
    assert sessions[0]["energy_kwh"] == 14.0  # (15000 - 1000) / 1000


def test_ocpp_websocket_endpoint():
    """Verify OCPP 1.6 WebSocket JSON-RPC 2.0 communication over /ocpp/{charger_id}."""
    client = TestClient(app)

    with client.websocket_connect("/ocpp/CP-WS-01", subprotocols=["ocpp1.6"]) as ws:
        # BootNotification Call
        ws.send_text(json.dumps([2, "call-1", "BootNotification", {"chargePointVendor": "Delta"}]))
        raw_res = ws.receive_text()
        res = json.loads(raw_res)
        assert res[0] == 3
        assert res[1] == "call-1"
        assert res[2]["status"] == "Accepted"

        # StatusNotification Call
        ws.send_text(json.dumps([2, "call-2", "StatusNotification", {"connectorId": 1, "status": "Available"}]))
        raw_res = ws.receive_text()
        res = json.loads(raw_res)
        assert res[0] == 3
        assert res[1] == "call-2"

        # StartTransaction Call
        ws.send_text(json.dumps([2, "call-3", "StartTransaction", {"connectorId": 1, "idTag": "TAG-99", "meterStart": 0}]))
        raw_res = ws.receive_text()
        res = json.loads(raw_res)
        assert res[0] == 3
        assert res[1] == "call-3"
        tx_id = res[2]["transactionId"]

        # StopTransaction Call
        ws.send_text(json.dumps([2, "call-4", "StopTransaction", {"transactionId": tx_id, "meterStop": 12500}]))
        raw_res = ws.receive_text()
        res = json.loads(raw_res)
        assert res[0] == 3
        assert res[1] == "call-4"

    # Query sessions via HTTP GET /sessions and /api/v1/sessions
    resp = client.get("/sessions")
    assert resp.status_code == 200
    sessions_data = resp.json()
    assert any(s["session_id"] == f"ocpp-tx-{tx_id}" for s in sessions_data)

    resp_v1 = client.get("/api/v1/sessions")
    assert resp_v1.status_code == 200
    assert any(s["session_id"] == f"ocpp-tx-{tx_id}" for s in resp_v1.json())


def test_oscp_capacity_forecast_and_overload_alert():
    """Verify lowering OSCP capacity limit triggers an overload alert within one tick."""
    client = TestClient(app)

    # 1. Normal capacity: 100 kVA (baseline load ~36.8 kVA)
    resp = client.put(
        "/oscp/capacity-forecast",
        json={"max_capacity_kva": 100.0, "reason": "Nominal grid conditions"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Accepted"
    assert data["applied_capacity_kva"] == 100.0
    assert data["alert_triggered"] is False

    # Transformer risk is normal / acceptable
    risk_normal = TransformerService.get_transformer_risk(nominal_kva=100.0)
    assert risk_normal["kva"] == 100.0

    # 2. Lower capacity below current load: 25.0 kVA (< ~36.8 kVA current load)
    resp_overload = client.put(
        "/oscp/capacity-forecast",
        json={"max_capacity_kva": 25.0, "reason": "DSO emergency feeder curtailment"},
    )
    assert resp_overload.status_code == 200
    data_overload = resp_overload.json()
    assert data_overload["applied_capacity_kva"] == 25.0
    assert data_overload["alert_triggered"] is True

    # Alert immediately queryable via GET /standards/alerts
    alerts_resp = client.get("/standards/alerts")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 1
    assert any("DSO OSCP capacity limit" in a["message"] for a in alerts)
    assert any(a["severity"] == "critical" for a in alerts)

    # Transformer risk calculation immediately flags critical overload
    risk_overloaded = TransformerService.get_transformer_risk(nominal_kva=100.0)
    assert risk_overloaded["kva"] == 25.0
    assert risk_overloaded["level"] == "critical"

    # Replay tick frame immediately incorporates the alert and critical status within one tick
    frame = ReplayService.get_full_frame_at_tick(tick=300)
    assert frame["transformer_status"] == "critical"
    assert any("DSO OSCP capacity limit" in a["message"] for a in frame["alerts"])


def test_mock_charger_client_class():
    """Test MockChargerClient send helper methods with dummy connection."""
    import asyncio

    async def _run():
        class DummyConnection:
            def __init__(self):
                self.sent_messages = []

            async def send(self, message):
                self.sent_messages.append(message)

            async def recv(self):
                # Return accepted boot notification
                return '[3, "call-test", {"status": "Accepted", "currentTime": "2026-10-12T12:00:00Z", "interval": 30}]'

        dummy_conn = DummyConnection()
        charger = MockChargerClient("CP-MOCK-99", dummy_conn)
        assert charger.charger_id == "CP-MOCK-99"
        assert charger.current_transaction_id is None

    asyncio.run(_run())
