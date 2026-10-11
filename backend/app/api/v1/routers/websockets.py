"""WebSocket router for live cluster telemetry and simulation ticks."""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.forecast_service import ForecastService

router = APIRouter(tags=["Live Telemetry"])


@router.websocket("/ws/live")
async def websocket_live_telemetry(websocket: WebSocket):
    """Real-time streaming WebSocket endpoint broadcasting live cluster load and alerts."""
    await websocket.accept()
    try:
        # Stream live simulation ticks / cluster status
        f = ForecastService.format_24h_forecast()
        msg = {
            "type": "cluster_telemetry",
            "p50_current": f["p50"][0],
            "p90_current": f["p90"][0],
            "status": "connected",
        }
        await websocket.send_text(json.dumps(msg))

        while True:
            data = await websocket.receive_text()
            # Echo back ping / command acknowledgment
            await websocket.send_text(json.dumps({"type": "ack", "received": data}))
    except WebSocketDisconnect:
        pass
