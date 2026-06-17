# Pérez Hernández Ricardo — Práctica 8
# geo-api/main.py — Puerto: 8003
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Geo & Alert API")
os.environ["PORT"] = "8003"

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
    # Aquí interactuaría con la API de Google Maps
    return {"ok": True, "msg": f"Coordenadas actualizadas para {geo.usuario}"}

@app.post("/emergency")
def trigger_emergency(alert: EmergencyAlert):
    _active_alerts.append(alert)
    # Lógica de broadcasting de protección/emergencia
    return {"ok": True, "alert_status": "BROADCASTING", "data": alert}