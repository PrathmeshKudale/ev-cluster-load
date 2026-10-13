"""Standards router for OCPP 1.6J WebSocket protocol and OSCP 2.0 DSO capacity forecasts."""
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse

from app.api.v1.schemas import (
    OscpCapacityForecastRequest,
    OscpCapacityForecastResponse,
    SessionSummarySchema,
)
from app.services.ocpp_service import OcppService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Standards"])


# ==============================================================================
# OSCP (Open Smart Charging Protocol) Endpoints
# ==============================================================================

@router.put(
    "/oscp/capacity-forecast",
    response_model=OscpCapacityForecastResponse,
    summary="Update transformer capacity limit via OSCP 2.0 DSO forecast",
)
async def put_oscp_capacity_forecast(body: OscpCapacityForecastRequest):
    """
    Allow Distribution System Operator (DSO) or external grid controller to publish
    dynamic time-varying capacity limits. If the limit drops below current cluster load,
    an overload alert is immediately triggered within one tick.
    """
    result = OcppService.set_dso_capacity_forecast(
        max_capacity_kva=body.max_capacity_kva,
        forecast_hours=body.forecast_hours,
        reason=body.reason,
    )
    return result


@router.get(
    "/oscp/capacity-forecast",
    summary="Get active OSCP transformer capacity limits and overload status",
)
async def get_oscp_capacity_status():
    """Retrieve active DSO capacity limit, current cluster load, and any active alerts."""
    limit_kva = OcppService.get_dso_capacity_limit()
    current_load_kva = OcppService.get_current_load_kva()
    alerts = OcppService.get_active_alerts()
    return {
        "active_capacity_limit_kva": limit_kva,
        "current_load_kva": current_load_kva,
        "overload_risk": current_load_kva > limit_kva,
        "active_alerts": alerts,
    }


# ==============================================================================
# Sessions & Telemetry Endpoints
# ==============================================================================

@router.get(
    "/sessions",
    response_model=List[SessionSummarySchema],
    summary="List active and completed charging sessions",
)
async def get_sessions():
    """List active in-progress and completed EV charging sessions across all chargers."""
    return OcppService.get_sessions_summary()


@router.get(
    "/standards/chargers",
    summary="List connected OCPP 1.6 chargers and their real-time status",
)
async def get_connected_chargers():
    """List online OCPP 1.6 connected charge points."""
    return OcppService.get_chargers_summary()


@router.get(
    "/standards/alerts",
    summary="List active standards and grid capacity alerts",
)
async def get_standards_alerts():
    """List active overload alerts triggered by OSCP capacity changes."""
    return OcppService.get_active_alerts()


# ==============================================================================
# OCPP 1.6J WebSocket Central System Endpoint
# ==============================================================================

@router.websocket("/ocpp/{charger_id}")
async def websocket_ocpp_central_system(websocket: WebSocket, charger_id: str):
    """
    OCPP 1.6-J Central System WebSocket endpoint.
    Accepts charge points connecting with subprotocol 'ocpp1.6'.
    Processes:
    - BootNotification
    - StatusNotification
    - StartTransaction
    - MeterValues
    - StopTransaction
    """
    # Accept subprotocol ocpp1.6 if negotiated
    subprotocols = websocket.scope.get("subprotocols", [])
    selected_subprotocol = "ocpp1.6" if "ocpp1.6" in subprotocols else None
    await websocket.accept(subprotocol=selected_subprotocol)

    logger.info("OCPP Charge point connected: %s (subprotocol=%s)", charger_id, selected_subprotocol)

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
            except Exception as e:
                logger.error("[%s] Invalid JSON received: %s", charger_id, e)
                continue

            # OCPP 1.6 JSON message format:
            # CALL: [2, "<UniqueId>", "<Action>", {<Payload>}]
            if isinstance(msg, list) and len(msg) >= 3 and msg[0] == 2:
                unique_id = msg[1]
                action = msg[2]
                payload = msg[3] if len(msg) > 3 and isinstance(msg[3], dict) else {}

                response_payload = OcppService.handle_ocpp_call(charger_id, action, payload)

                # CALL_RESULT: [3, "<UniqueId>", {<Payload>}]
                reply = [3, unique_id, response_payload]
                await websocket.send_text(json.dumps(reply))
            else:
                logger.warning("[%s] Unsupported OCPP frame format: %s", charger_id, msg)

    except WebSocketDisconnect:
        logger.info("OCPP Charge point disconnected: %s", charger_id)
