# app/services/notify.py
from fastapi import WebSocket
from typing import List
from app.schemas.notify import NotificationIn, NotificationOut


class ConnectionManager:
    """"ConnectionManager handles all WebSocket client connections"""
    def __init__(self):
        # Store all active client WebSocket connections
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accepts a new WebSocket connection and adds it to the active pool.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Removes a WebSocket connection from the active pool.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: NotificationOut, websocket: WebSocket):
        """
        Sends a personal message to a specific client.
        """
        await websocket.send_text(f"Personal message: {message.json()}")

    async def broadcast(self, message: NotificationOut):
        """
        Sends a message to all connected clients.
        """
        for connection in self.active_connections:
            await connection.send_text(f"Broadcast message: {message.json()}")
