"""WebSocket router for live cluster telemetry and accelerated simulation replay streaming."""
import asyncio
import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.forecast_service import ForecastService
from app.services.replay_service import ReplayService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Live Telemetry"])


@router.websocket("/ws/live")
async def websocket_live_telemetry(websocket: WebSocket):
    """Real-time streaming WebSocket endpoint broadcasting live cluster load and alerts."""
    await websocket.accept()
    try:
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
            await websocket.send_text(json.dumps({"type": "ack", "received": data}))
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/replay")
async def websocket_replay_stream(websocket: WebSocket):
    """
    Accelerated historical day simulation replay WebSocket.
    Streams recorded minute frames at speeds from 1x up to 1440x (a full 24h day in ~60 seconds).
    Accepts commands: start, pause, resume, seek, speed, reset.
    """
    await websocket.accept()

    # Send initial connection frame and state
    state = ReplayService.get_state()
    init_frame = ReplayService.get_full_frame_at_tick()
    await websocket.send_text(json.dumps({"type": "replay_connected", "state": state, "frame": init_frame}))

    stop_event = asyncio.Event()

    async def sender_loop():
        """Continuously streams simulation ticks at chosen speed multiplier."""
        while not stop_event.is_set():
            st = ReplayService.get_state()
            if st["status"] == "running":
                frame = ReplayService.get_full_frame_at_tick()
                try:
                    await websocket.send_text(json.dumps(frame))
                except Exception:
                    break

                # Advance tick
                ReplayService.tick(steps=1)

                # Delay per tick: At 1440x speed, 1440 minutes streamed in 60s -> ~0.0416s delay
                mult = max(1.0, float(st.get("speed_multiplier", 60.0)))
                # At 1440x, 60s / 1440 = ~0.0416s
                delay = max(0.015, min(60.0 / mult, 1.0))
                await asyncio.sleep(delay)
            elif st["status"] == "completed":
                try:
                    await websocket.send_text(json.dumps({
                        "type": "replay_complete",
                        "tick": st["current_tick"],
                        "message": "Full-day replay completed.",
                    }))
                except Exception:
                    pass
                await asyncio.sleep(0.5)
            else:
                # Paused or stopped
                await asyncio.sleep(0.1)

    async def receiver_loop():
        """Listens for user playback commands (start, pause, resume, seek, speed)."""
        while not stop_event.is_set():
            try:
                raw = await websocket.receive_text()
                data = json.loads(raw)
                action = data.get("action") or data.get("type")

                if action in ("start", "play"):
                    speed = float(data.get("speed", data.get("speed_multiplier", 1440.0)))
                    horizon = int(data.get("horizon_hours", 24))
                    ReplayService.start_replay(speed_multiplier=speed, horizon_hours=horizon)
                    state = ReplayService.get_state()
                    await websocket.send_text(json.dumps({"type": "state_changed", "state": state}))

                elif action == "pause":
                    ReplayService.pause()
                    state = ReplayService.get_state()
                    await websocket.send_text(json.dumps({"type": "state_changed", "state": state}))

                elif action == "resume":
                    ReplayService.resume()
                    state = ReplayService.get_state()
                    await websocket.send_text(json.dumps({"type": "state_changed", "state": state}))

                elif action == "seek":
                    target_tick = int(data.get("tick", 0))
                    ReplayService.seek(target_tick)
                    frame = ReplayService.get_full_frame_at_tick()
                    await websocket.send_text(json.dumps(frame))

                elif action in ("speed", "set_speed"):
                    speed = float(data.get("speed", data.get("speed_multiplier", 60.0)))
                    ReplayService.set_speed(speed)
                    state = ReplayService.get_state()
                    await websocket.send_text(json.dumps({"type": "state_changed", "state": state}))

                elif action in ("stop", "reset"):
                    ReplayService.stop()
                    frame = ReplayService.get_full_frame_at_tick(0)
                    await websocket.send_text(json.dumps(frame))

            except WebSocketDisconnect:
                stop_event.set()
                break
            except Exception as e:
                logger.debug("Replay WebSocket receive error: %s", e)

    try:
        sender_task = asyncio.create_task(sender_loop())
        receiver_task = asyncio.create_task(receiver_loop())

        done, pending = await asyncio.wait(
            [sender_task, receiver_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except WebSocketDisconnect:
        pass
    finally:
        stop_event.set()
