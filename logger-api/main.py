# Pérez Hernández Ricardo — Práctica 8
# logger-api/main.py — Puerto: 7000
import os
import time
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Logger API")
os.environ["PORT"] = "7000"

class LogEntry(BaseModel):
    service: str
    level: str  # INFO, WARNING, ERROR
    message: str

_logs = []

@app.get("/health")
def health():
    return {"status": "ok", "service": "logger-api"}

@app.post("/log")
def add_log(entry: LogEntry):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_string = f"[{timestamp}] [{entry.service.upper()}] [{entry.level}] {entry.message}"
    _logs.append(log_string)
    print(log_string, flush=True)  # Visible en docker logs p8-logger-api
    return {"ok": True}

@app.get("/logs")
def get_logs(limit: int = 50):
    return {"logs": _logs[-limit:]}