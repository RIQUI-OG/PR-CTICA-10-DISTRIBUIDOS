# geo-api/main.py — Puerto: 8003
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <--- ESTO ES VITAL
from pydantic import BaseModel

app = FastAPI(title="Geo & Alert API")
os.environ["PORT"] = "8003"

# ESTO DEBE IR AQUÍ (ANTES DE LAS RUTAS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GeoLocation(BaseModel):
    usuario: str
    lat: float
    lng: float

class EmergencyAlert(BaseModel):
    usuario: str
    tipo_alerta: str
    audio_stream_url: str = None

_active_alerts = []

@app.get("/health")
def health():
    return {"status": "ok", "service": "geo-api"}

@app.post("/location")
def update_location(geo: GeoLocation):
    return {"ok": True, "msg": f"Coordenadas actualizadas para {geo.usuario}"}

@app.post("/emergency")
def trigger_emergency(alert: EmergencyAlert):
    _active_alerts.append(alert)
    return {"ok": True, "alert_status": "BROADCASTING", "data": alert}
