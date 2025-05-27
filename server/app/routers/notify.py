# app/routers/notify.py
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.schemas.notify import NotificationIn, NotificationOut
from app.services.notify import ConnectionManager
logger = logging.getLogger(__name__)


router = APIRouter()
manager = ConnectionManager()

@router.websocket("/notify")
async def websocket_notify(websocket:WebSocket):
    """
    WebSocket endpoint for sending/receiving notifications.
    """
    logger.info("WebSocket connection established!!!!!!!!!!!!!")
    await manager.connect(websocket)
    try:
        while True:
            # Receive a message from the client
            data = await websocket.receive_text()

            try:
                # Parse client message using schema
                parsed = NotificationIn.parse_raw(data) # data is a JSON string that comes from the frontend (via WebSocket)
            except Exception as e:
                # Send error if format is invalid
                error_msg = NotificationOut(
                    type="personal",
                    content="Invalid message format. Please check your input."
                )
                await manager.send_personal_message(error_msg, websocket)
                continue

            # Send confirmation to sender
            personal_msg = NotificationOut(
                type="personal",
                content=f"Received your message: {parsed.type}: {parsed.content}"
            )
            await manager.send_personal_message(personal_msg, websocket)

            # Broadcast the message to all connected clients
            broadcast_msg = NotificationOut(
                type="broadcast",
                content=f"Bradcast message: {parsed.type}: {parsed.content}"
            )
            await manager.broadcast(broadcast_msg)
    except WebSocketDisconnect:
        # Handle disconnect
        manager.disconnect(websocket)
        disconnect_msg = NotificationOut(
            type="system",
            content="A client has disconnected."
        )
        await manager.broadcast(disconnect_msg)

