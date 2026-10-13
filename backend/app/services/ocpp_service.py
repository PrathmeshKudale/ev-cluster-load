"""OCPP 1.6J Central System service and message processor.

Handles OCPP 1.6 JSON WebSocket protocol messages:
- BootNotification
- StatusNotification
- StartTransaction
- MeterValues
- StopTransaction

Stores sessions and real-time load so they are immediately visible in cluster and station metrics.
Integrates with OSCP (Open Smart Charging Protocol) for DSO capacity limit forecasts.
"""
from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OcppService:
    """In-memory and persistent coordinator for OCPP 1.6J chargers, transactions, load, and OSCP limits."""

    _active_chargers: Dict[str, Dict[str, Any]] = {}
    _transactions: Dict[int, Dict[str, Any]] = {}
    _completed_sessions: List[Dict[str, Any]] = []
    _active_alerts: List[Dict[str, Any]] = []
    _tx_counter: int = 1000
    _dso_capacity_override_kva: Optional[float] = None
    _dso_capacity_forecast_24h: Optional[List[float]] = None

    @classmethod
    def reset(cls) -> None:
        """Reset internal state (useful for test isolation)."""
        cls._active_chargers.clear()
        cls._transactions.clear()
        cls._completed_sessions.clear()
        cls._active_alerts.clear()
        cls._tx_counter = 1000
        cls._dso_capacity_override_kva = None
        cls._dso_capacity_forecast_24h = None

    @classmethod
    def get_current_load_kva(cls, default_baseline_kw: float = 35.0, power_factor: float = 0.95) -> float:
        """Compute aggregate real-time load in kVA from active chargers and baseline cluster load."""
        charger_power_kw = sum(c.get("active_power_kw", 0.0) for c in cls._active_chargers.values())
        tx_power_kw = sum(tx.get("current_power_kw", 0.0) for tx in cls._transactions.values())
        active_kw = max(charger_power_kw, tx_power_kw)
        total_kw = default_baseline_kw + active_kw
        return round(float(total_kw / power_factor), 2)

    @classmethod
    def get_dso_capacity_limit(cls, default_kva: float = 100.0) -> float:
        """Get the active transformer capacity limit, respecting any DSO OSCP forecast override."""
        if cls._dso_capacity_override_kva is not None:
            return cls._dso_capacity_override_kva
        return default_kva

    @classmethod
    def get_active_alerts(cls) -> List[Dict[str, Any]]:
        """Retrieve active system alerts, including OSCP capacity violations."""
        return list(cls._active_alerts)

    @classmethod
    def clear_alerts(cls) -> None:
        """Clear active alerts."""
        cls._active_alerts.clear()

    @classmethod
    def set_dso_capacity_forecast(
        cls,
        max_capacity_kva: float,
        forecast_hours: Optional[List[float]] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply OSCP capacity forecast from operator or distribution grid company (DSO)."""
        cls._dso_capacity_override_kva = max(10.0, float(max_capacity_kva))
        if forecast_hours and len(forecast_hours) == 24:
            cls._dso_capacity_forecast_24h = [float(x) for x in forecast_hours]
        else:
            cls._dso_capacity_forecast_24h = [cls._dso_capacity_override_kva] * 24

        now_dt = datetime.now(timezone.utc)
        current_load = cls.get_current_load_kva()

        # Check if limit drops below current cluster load -> trigger immediate overload alert within 1 tick
        alert_triggered = False
        if cls._dso_capacity_override_kva < current_load:
            alert = {
                "id": f"ALT-OSCP-{int(now_dt.timestamp())}",
                "severity": "critical",
                "entity_type": "transformer",
                "entity_id": "T1",
                "message": (
                    f"DSO OSCP capacity limit ({cls._dso_capacity_override_kva:.1f} kVA) "
                    f"dropped below current load ({current_load:.1f} kVA)! Overload risk."
                ),
                "limit_kva": cls._dso_capacity_override_kva,
                "current_load_kva": current_load,
                "timestamp": now_dt.isoformat(),
            }
            cls._active_alerts.append(alert)
            alert_triggered = True

        return {
            "status": "Accepted",
            "applied_capacity_kva": cls._dso_capacity_override_kva,
            "current_load_kva": current_load,
            "alert_triggered": alert_triggered,
            "forecast_hours": cls._dso_capacity_forecast_24h,
            "reason": reason or "DSO capacity forecast limit applied",
            "timestamp": now_dt.isoformat(),
        }

    @classmethod
    def handle_ocpp_call(cls, charger_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming OCPP 1.6 Call payload and return CallResult payload."""
        now_iso = datetime.now(timezone.utc).isoformat()

        if action == "BootNotification":
            cls._active_chargers[charger_id] = {
                "charger_id": charger_id,
                "vendor": payload.get("chargePointVendor", "Generic"),
                "model": payload.get("chargePointModel", "EVSE-1.6"),
                "firmware": payload.get("firmwareVersion", "1.0.0"),
                "status": "Available",
                "connected_at": now_iso,
                "active_power_kw": 0.0,
            }
            return {
                "status": "Accepted",
                "currentTime": now_iso,
                "interval": 30,
            }

        elif action == "StatusNotification":
            status_val = payload.get("status", "Available")
            if charger_id not in cls._active_chargers:
                cls._active_chargers[charger_id] = {
                    "charger_id": charger_id,
                    "connected_at": now_iso,
                }
            cls._active_chargers[charger_id]["status"] = status_val
            cls._active_chargers[charger_id]["error_code"] = payload.get("errorCode", "NoError")
            cls._active_chargers[charger_id]["last_status_time"] = now_iso
            return {}

        elif action == "StartTransaction":
            cls._tx_counter += 1
            tx_id = cls._tx_counter
            connector_id = payload.get("connectorId", 1)
            id_tag = payload.get("idTag", "TAG-ANON")
            meter_start = payload.get("meterStart", 0)

            tx_data = {
                "transaction_id": tx_id,
                "charger_id": charger_id,
                "connector_id": connector_id,
                "id_tag": id_tag,
                "start_time": payload.get("timestamp", now_iso),
                "meter_start": meter_start,
                "current_power_kw": 7.4,  # Standard AC charging rate
                "energy_kwh": 0.0,
                "status": "Active",
            }
            cls._transactions[tx_id] = tx_data

            if charger_id in cls._active_chargers:
                cls._active_chargers[charger_id]["status"] = "Charging"
                cls._active_chargers[charger_id]["active_transaction_id"] = tx_id
                cls._active_chargers[charger_id]["active_power_kw"] = 7.4

            return {
                "transactionId": tx_id,
                "idTagInfo": {"status": "Accepted"},
            }

        elif action == "MeterValues":
            tx_id = payload.get("transactionId")
            power_kw = 7.4
            energy_wh = None

            # Parse sampled values if provided
            meter_values = payload.get("meterValue", [])
            for mv in meter_values:
                for sampled in mv.get("sampledValue", []):
                    measurand = sampled.get("measurand", "Energy.Active.Import.Register")
                    val_str = str(sampled.get("value", "0"))
                    try:
                        val_num = float(val_str)
                        if "Power" in measurand:
                            power_kw = val_num if val_num < 1000 else val_num / 1000.0
                        elif "Energy" in measurand:
                            energy_wh = val_num
                    except ValueError:
                        pass

            if tx_id and tx_id in cls._transactions:
                cls._transactions[tx_id]["current_power_kw"] = power_kw
                if energy_wh is not None:
                    start_wh = cls._transactions[tx_id]["meter_start"]
                    cls._transactions[tx_id]["energy_kwh"] = max(0.0, (energy_wh - start_wh) / 1000.0)

            if charger_id in cls._active_chargers:
                cls._active_chargers[charger_id]["active_power_kw"] = power_kw

            return {}

        elif action == "StopTransaction":
            tx_id = payload.get("transactionId")
            meter_stop = payload.get("meterStop", 0)
            stop_time = payload.get("timestamp", now_iso)
            reason = payload.get("reason", "Local")

            session_record = None
            if tx_id and tx_id in cls._transactions:
                tx_data = cls._transactions.pop(tx_id)
                meter_start = tx_data.get("meter_start", 0)
                energy_kwh = max(0.5, (meter_stop - meter_start) / 1000.0) if meter_stop > meter_start else 12.5

                session_record = {
                    "session_id": f"ocpp-tx-{tx_id}",
                    "charger_id": charger_id,
                    "id_tag": tx_data.get("id_tag", "UNKNOWN"),
                    "start_time": tx_data.get("start_time"),
                    "stop_time": stop_time,
                    "energy_kwh": round(energy_kwh, 2),
                    "reason": reason,
                    "status": "Completed",
                }
                cls._completed_sessions.append(session_record)
                cls._persist_session_safe(session_record)

            if charger_id in cls._active_chargers:
                cls._active_chargers[charger_id]["status"] = "Available"
                cls._active_chargers[charger_id]["active_power_kw"] = 0.0
                cls._active_chargers[charger_id].pop("active_transaction_id", None)

            return {
                "idTagInfo": {"status": "Accepted"},
            }

        else:
            logger.warning("Unrecognized OCPP 1.6 action: %s", action)
            return {}

    @classmethod
    def _persist_session_safe(cls, session_dict: Dict[str, Any]) -> None:
        """Safely attempt to persist completed session to database without crashing if DB unavailable."""
        try:
            from app.db.connection import SessionLocal
            from app.db.models import Session as DbSession
            import hashlib

            with SessionLocal() as db:
                user_id_hash = hashlib.sha256(session_dict.get("id_tag", "ANON").encode()).hexdigest()
                start_dt = datetime.fromisoformat(session_dict["start_time"].replace("Z", "+00:00"))
                stop_dt = datetime.fromisoformat(session_dict["stop_time"].replace("Z", "+00:00"))

                db_sess = DbSession(
                    id=session_dict["session_id"],
                    charger_id=session_dict["charger_id"],
                    station_id="S1",  # Default mapped station
                    user_hash=user_id_hash,
                    start_time=start_dt,
                    end_time=stop_dt,
                    kwh_delivered=session_dict["energy_kwh"],
                )
                db.add(db_sess)
                db.commit()
                logger.info("Persisted OCPP session %s to database.", session_dict["session_id"])
        except Exception as e:
            logger.debug("Database session persistence bypassed (in-memory mode or unseeded schema): %s", e)

    @classmethod
    def get_chargers_summary(cls) -> List[Dict[str, Any]]:
        """List active connected OCPP chargers."""
        return list(cls._active_chargers.values())

    @classmethod
    def get_sessions_summary(cls) -> List[Dict[str, Any]]:
        """List active and completed OCPP sessions visible to dashboard."""
        sessions = []
        for tx in cls._transactions.values():
            sessions.append({
                "session_id": f"ocpp-tx-{tx['transaction_id']}",
                "charger_id": tx["charger_id"],
                "status": "In Progress",
                "power_kw": tx.get("current_power_kw", 7.4),
                "energy_kwh": tx.get("energy_kwh", 0.0),
                "start_time": tx.get("start_time"),
            })
        for cs in reversed(cls._completed_sessions[-20:]):
            sessions.append({
                "session_id": cs["session_id"],
                "charger_id": cs["charger_id"],
                "status": "Completed",
                "power_kw": 0.0,
                "energy_kwh": cs["energy_kwh"],
                "start_time": cs["start_time"],
                "stop_time": cs["stop_time"],
                "reason": cs.get("reason", "Local"),
            })
        return sessions
