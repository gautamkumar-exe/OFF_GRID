"""
Sentinel Omni — API Gateway & WebSocket Hub
Receives alerts from Edge Agents and broadcasts to all connected Dashboards.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import deque
import json
import asyncio
import shutil
import os
import sys
import base64
import cv2
import numpy as np
from datetime import datetime

# Add edge directory to path for AI engine access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "edge")))
from inference_engine import SentinelInferenceEngine

app = FastAPI(title="Sentinel Omni - API Gateway")

# Enable CORS for the Frontend (React Dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Initialize AI Engine ──
engine = SentinelInferenceEngine(
    yolo_model_path="../edge/best.pt",
    lstm_model_path="../edge/violence_lstm_model.h5"
)

# ── In-Memory Alert Storage ──
MAX_ALERT_HISTORY = 100
alert_history = deque(maxlen=MAX_ALERT_HISTORY)

# ── WebSocket Connection Manager ──
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[*] Dashboard connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[*] Dashboard disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# ── Alert Model ──
class ThreatAlert(BaseModel):
    id: str
    type: str  # 'weapon', 'violence', 'pose'
    camera_id: str
    location: str
    confidence: float
    timestamp: str
    thumbnail: str | None = None


# ── REST Endpoints ──
@app.get("/")
async def root():
    return {
        "status": "Sentinel Omni API Online",
        "connected_dashboards": len(manager.active_connections),
        "total_alerts": len(alert_history)
    }


@app.post("/api/v1/alerts")
async def receive_alert(alert: ThreatAlert):
    """Receive an alert from an Edge Agent and broadcast to all dashboards."""
    alert_dict = alert.model_dump()
    alert_json = json.dumps(alert_dict)

    # Store in history
    alert_history.appendleft(alert_dict)

    severity = "CRITICAL" if alert.type == "weapon" else "HIGH" if alert.type == "violence" else "INFO"
    print(f"[!] [{severity}] {alert.type.upper()}: {alert.location} — confidence {alert.confidence:.2%}")

    # Broadcast to all connected dashboards
    await manager.broadcast(alert_json)

    return {
        "status": "success",
        "notified": len(manager.active_connections)
    }


@app.get("/api/v1/alerts/history")
async def get_alert_history(limit: int = 50):
    """Return recent alert history for dashboard initial load."""
    alerts = list(alert_history)[:limit]
    return {
        "alerts": alerts,
        "total": len(alert_history)
    }


@app.get("/api/v1/stats")
async def get_stats():
    """Return real-time system statistics for the dashboard."""
    total = len(alert_history)
    weapon_alerts = sum(1 for a in alert_history if a["type"] == "weapon")
    violence_alerts = sum(1 for a in alert_history if a["type"] == "violence")
    
    # Calculate average confidence
    confidences = [a["confidence"] for a in alert_history]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    return {
        "total_alerts": total,
        "weapon_alerts": weapon_alerts,
        "violence_alerts": violence_alerts,
        "active_dashboards": len(manager.active_connections),
        "avg_confidence": round(avg_confidence, 4)
    }


# ── WebSocket Endpoint ──
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket for Dashboards to receive real-time alert streams."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo heartbeat
            await websocket.send_text(json.dumps({"type": "heartbeat", "status": "active"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/v1/analyze/live")
async def analyze_live_frame(payload: dict):
    """Analyze a single frame from a live camera stream."""
    try:
        frame_data = payload.get("frame")
        if not frame_data:
            return {"error": "No frame data provided"}
        
        # Decode base64 frame
        if "," in frame_data:
            frame_data = frame_data.split(",")[1]
            
        img_bytes = base64.b64decode(frame_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Failed to decode frame"}
            
        # Run inference
        detections, _ = engine.process_frame(frame)
        
        # Calculate aggregate threat level
        threat_level = 0.0
        for d in detections:
            if d['type'] in ['weapon', 'violence']:
                threat_level = max(threat_level, d['confidence'])
        
        return {
            "threat_level": round(threat_level, 4),
            "detections": detections,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/v1/analyze/video")
async def analyze_video(file: UploadFile = File(...)):
    """Upload a video and get a temporal threat analysis report."""
    temp_dir = "temp_analysis"
    os.makedirs(temp_dir, exist_ok=True)
    
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Run forensic analysis
        # We run this in a threadpool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(None, engine.analyze_video_file, file_path)
        
        return report
        
    except Exception as e:
        return {"error": str(e)}
        
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("   SENTINEL OMNI — API Gateway")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
