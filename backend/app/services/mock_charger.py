"""Mock OCPP 1.6J EVSE Charger Client.

Uses the official Python `ocpp` library to simulate real EV charging stations connecting to Central Systems:
- Connects via WebSocket with subprotocol `ocpp1.6`
- Sends BootNotification, StatusNotification, StartTransaction, MeterValues, StopTransaction
- Tracks active sessions and meter updates
"""
import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional

import websockets
from ocpp.v16 import ChargePoint
from ocpp.v16 import call
from ocpp.v16.enums import ChargePointStatus, RegistrationStatus

logger = logging.getLogger(__name__)


class MockChargerClient(ChargePoint):
    """OCPP 1.6J compliant simulated EVSE charger client."""

    def __init__(self, charger_id: str, connection: Any):
        super().__init__(charger_id, connection)
        self.charger_id = charger_id
        self.current_transaction_id: Optional[int] = None

    async def send_boot_notification(
        self,
        vendor: str = "ABB",
        model: str = "Terra-54-Tri",
        firmware: str = "v2.4.1",
    ) -> Any:
        """Send BootNotification to Central System upon startup."""
        req = call.BootNotification(
            charge_point_vendor=vendor,
            charge_point_model=model,
            firmware_version=firmware,
        )
        res = await self.call(req)
        logger.info("[%s] BootNotification response: status=%s", self.charger_id, res.status)
        return res

    async def send_status_notification(
        self,
        status: str = ChargePointStatus.available,
        connector_id: int = 1,
        error_code: str = "NoError",
    ) -> Any:
        """Send StatusNotification updating connector availability state."""
        req = call.StatusNotification(
            connector_id=connector_id,
            error_code=error_code,
            status=status,
        )
        res = await self.call(req)
        logger.info("[%s] StatusNotification (%s) sent", self.charger_id, status)
        return res

    async def send_start_transaction(
        self,
        connector_id: int = 1,
        id_tag: str = "USER-RFID-001",
        meter_start: int = 0,
    ) -> Any:
        """Send StartTransaction when driver plugs in and initiates charging session."""
        now_iso = datetime.now(timezone.utc).isoformat()
        req = call.StartTransaction(
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=meter_start,
            timestamp=now_iso,
        )
        res = await self.call(req)
        self.current_transaction_id = res.transaction_id
        logger.info(
            "[%s] StartTransaction accepted: tx_id=%s, id_tag_status=%s",
            self.charger_id,
            res.transaction_id,
            getattr(res.id_tag_info, "status", "Accepted"),
        )
        return res

    async def send_meter_values(
        self,
        transaction_id: Optional[int] = None,
        power_kw: float = 7.4,
        energy_wh: int = 15000,
        connector_id: int = 1,
    ) -> Any:
        """Send MeterValues telemetry with active power (kW) and energy register (Wh)."""
        tx_id = transaction_id if transaction_id is not None else self.current_transaction_id
        now_iso = datetime.now(timezone.utc).isoformat()
        req = call.MeterValues(
            connector_id=connector_id,
            transaction_id=tx_id,
            meter_value=[
                {
                    "timestamp": now_iso,
                    "sampled_value": [
                        {
                            "value": str(power_kw),
                            "context": "Sample.Periodic",
                            "format": "Raw",
                            "measurand": "Power.Active.Import",
                            "unit": "kW",
                        },
                        {
                            "value": str(energy_wh),
                            "context": "Sample.Periodic",
                            "format": "Raw",
                            "measurand": "Energy.Active.Import.Register",
                            "unit": "Wh",
                        },
                    ],
                }
            ],
        )
        res = await self.call(req)
        logger.info("[%s] MeterValues sent: %s kW, %s Wh", self.charger_id, power_kw, energy_wh)
        return res

    async def send_stop_transaction(
        self,
        transaction_id: Optional[int] = None,
        meter_stop: int = 15000,
        reason: str = "Local",
    ) -> Any:
        """Send StopTransaction when session completes or vehicle disconnects."""
        tx_id = transaction_id if transaction_id is not None else self.current_transaction_id
        now_iso = datetime.now(timezone.utc).isoformat()
        req = call.StopTransaction(
            transaction_id=tx_id or 1001,
            meter_stop=meter_stop,
            timestamp=now_iso,
            reason=reason,
        )
        res = await self.call(req)
        logger.info("[%s] StopTransaction completed: tx_id=%s", self.charger_id, tx_id)
        self.current_transaction_id = None
        return res


async def run_mock_charging_session(
    ws_url: str = "ws://localhost:8000/ocpp/CP-101",
    charger_id: str = "CP-101",
    vendor: str = "ABB",
    model: str = "Terra-54-Tri",
    id_tag: str = "TAG-EV-9999",
    power_kw: float = 7.4,
    energy_kwh: float = 14.8,
    delay_between_steps: float = 0.1,
) -> Dict[str, Any]:
    """
    Execute a complete mock charging lifecycle over WebSocket:
    1. BootNotification
    2. StatusNotification (Available)
    3. StartTransaction
    4. StatusNotification (Charging)
    5. MeterValues (active power & Wh)
    6. StopTransaction
    7. StatusNotification (Available)
    """
    async with websockets.connect(ws_url, subprotocols=["ocpp1.6"]) as ws:
        client = MockChargerClient(charger_id, ws)
        router_task = asyncio.create_task(client.start())

        try:
            # 1. BootNotification
            boot_res = await client.send_boot_notification(vendor=vendor, model=model)
            await asyncio.sleep(delay_between_steps)

            # 2. StatusNotification -> Available
            await client.send_status_notification(status="Available")
            await asyncio.sleep(delay_between_steps)

            # 3. StartTransaction
            start_res = await client.send_start_transaction(id_tag=id_tag, meter_start=0)
            tx_id = start_res.transaction_id
            await asyncio.sleep(delay_between_steps)

            # 4. StatusNotification -> Charging
            await client.send_status_notification(status="Charging")
            await asyncio.sleep(delay_between_steps)

            # 5. MeterValues
            energy_wh = int(energy_kwh * 1000)
            await client.send_meter_values(transaction_id=tx_id, power_kw=power_kw, energy_wh=energy_wh)
            await asyncio.sleep(delay_between_steps)

            # 6. StopTransaction
            stop_res = await client.send_stop_transaction(transaction_id=tx_id, meter_stop=energy_wh, reason="Local")
            await asyncio.sleep(delay_between_steps)

            # 7. StatusNotification -> Available
            await client.send_status_notification(status="Available")

            return {
                "status": "success",
                "charger_id": charger_id,
                "transaction_id": tx_id,
                "energy_kwh": energy_kwh,
                "power_kw": power_kw,
                "id_tag": id_tag,
            }
        finally:
            router_task.cancel()
            try:
                await router_task
            except asyncio.CancelledError:
                pass
