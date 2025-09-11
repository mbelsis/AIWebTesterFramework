import asyncio
import json
import time
import threading
from typing import Dict, Optional, Any
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from utils.ports import find_free_port

class ControlRoom:
    def __init__(self, port: Optional[int] = None):
        # Use dynamic port detection if no specific port provided
        if port is None:
            self.port = find_free_port(start=8788)
        else:
            self.port = port
        self.app = FastAPI(title="AI WebTester Control Room")
        self.connections: Dict[str, WebSocket] = {}
        self.run_states: Dict[str, Dict] = {}
        self.setup_routes()

    def setup_routes(self):
        @self.app.websocket("/ws/{run_id}")
        async def websocket_endpoint(websocket: WebSocket, run_id: str):
            await websocket.accept()
            self.connections[run_id] = websocket
            try:
                while True:
                    data = await websocket.receive_text()
                    command = json.loads(data)
                    await self.handle_command(run_id, command)
            except WebSocketDisconnect:
                del self.connections[run_id]

        @self.app.get("/api/runs")
        async def list_runs():
            return {"runs": list(self.run_states.keys())}

        @self.app.get("/api/runs/{run_id}")
        async def get_run_state(run_id: str):
            return self.run_states.get(run_id, {})

        # Serve frontend if exists
        frontend_dist = Path("control_room/frontend/dist")
        if frontend_dist.exists():
            self.app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    async def handle_command(self, run_id: str, command: Dict):
        """Handle commands from frontend"""
        cmd_type = command.get("cmd")
        if cmd_type in ["approve", "reject", "stop"]:
            # Store command for executor to pick up
            if run_id not in self.run_states:
                self.run_states[run_id] = {}
            self.run_states[run_id]["pending_command"] = command

    async def send_status(self, run_id: str, status: str, message: str = ""):
        """Send status update to frontend"""
        if run_id in self.connections:
            try:
                await self.connections[run_id].send_text(json.dumps({
                    "type": "status",
                    "status": status,
                    "message": message,
                    "timestamp": time.time()
                }))
            except:
                pass
        
        # Store in state
        if run_id not in self.run_states:
            self.run_states[run_id] = {}
        self.run_states[run_id]["status"] = status
        self.run_states[run_id]["message"] = message

    async def send_step(self, run_id: str, idx: int, title: str, status: str, error: str = ""):
        """Send step update to frontend"""
        if run_id in self.connections:
            try:
                await self.connections[run_id].send_text(json.dumps({
                    "type": "step",
                    "step_index": idx,
                    "title": title,
                    "status": status,
                    "error": error,
                    "timestamp": time.time()
                }))
            except:
                pass

    async def send_log(self, run_id: str, level: str, source: str, message: str, timestamp: float):
        """Send log message to frontend"""
        if run_id in self.connections:
            try:
                await self.connections[run_id].send_text(json.dumps({
                    "type": "log",
                    "level": level,
                    "source": source,
                    "message": message,
                    "timestamp": timestamp
                }))
            except:
                pass

    async def send_thumb_png(self, run_id: str, png_data: bytes, ts: float):
        """Send thumbnail screenshot to frontend"""
        if run_id in self.connections:
            try:
                import base64
                b64_data = base64.b64encode(png_data).decode()
                await self.connections[run_id].send_text(json.dumps({
                    "type": "thumbnail",
                    "data": b64_data,
                    "timestamp": ts
                }))
            except:
                pass

    async def wait_for_control(self, run_id: str, allowed_commands: set) -> Dict:
        """Wait for user command"""
        while True:
            if run_id in self.run_states and "pending_command" in self.run_states[run_id]:
                cmd = self.run_states[run_id].pop("pending_command")
                if cmd.get("cmd") in allowed_commands:
                    return cmd
            await asyncio.sleep(0.1)

    def start_in_background(self):
        """Start Control Room in background thread"""
        def run_server():
            uvicorn.run(self.app, host="127.0.0.1", port=self.port, log_level="warning")
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        time.sleep(1)  # Give server time to start

    def start(self):
        """Start Control Room in foreground"""
        uvicorn.run(self.app, host="127.0.0.1", port=self.port)

    def get_url(self) -> str:
        """Get the Control Room URL"""
        return f"http://127.0.0.1:{self.port}"