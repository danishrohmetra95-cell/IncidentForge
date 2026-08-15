"""SSE event streaming endpoint.

Server-Sent Events for live investigation updates.
No WebSocket — unidirectional server→client is sufficient.
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from packages.contracts.events import InvestigationEvent

logger = logging.getLogger("incidentforge.events")

router = APIRouter(prefix="/api", tags=["events"])

# ── Event bus (in-memory, per-incident) ──────────────────────────
# In production, this would use Redis pub/sub.

_event_queues: dict[str, list[asyncio.Queue]] = {}


def get_event_bus(incident_id: str) -> asyncio.Queue:
    """Create and register a new event queue for an SSE subscriber."""
    queue: asyncio.Queue = asyncio.Queue()
    if incident_id not in _event_queues:
        _event_queues[incident_id] = []
    _event_queues[incident_id].append(queue)
    return queue


def remove_event_bus(incident_id: str, queue: asyncio.Queue) -> None:
    if incident_id in _event_queues:
        try:
            _event_queues[incident_id].remove(queue)
        except ValueError:
            pass


async def publish_event(event: InvestigationEvent) -> None:
    """Publish an event to all subscribers for the incident."""
    queues = _event_queues.get(event.incident_id, [])
    for queue in queues:
        try:
            await queue.put(event)
        except Exception:
            logger.warning("Failed to publish event", exc_info=True)


async def create_event_listener(incident_id: str):
    """Create an event listener coroutine for the orchestrator."""
    async def listener(event: InvestigationEvent):
        await publish_event(event)
    return listener


# ── SSE endpoint ─────────────────────────────────────────────────

@router.get("/incidents/{incident_id}/events")
async def stream_events(incident_id: str):
    """Stream investigation events via Server-Sent Events."""

    async def event_generator():
        queue = get_event_bus(incident_id)
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({"incident_id": incident_id}),
            }

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event.event_type,
                        "data": json.dumps(event.model_dump(), default=str),
                    }
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"event": "keepalive", "data": "{}"}
        except asyncio.CancelledError:
            pass
        finally:
            remove_event_bus(incident_id, queue)

    return EventSourceResponse(event_generator())
