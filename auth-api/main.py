# Pérez Hernández Ricardo — Práctica 8
# auth-api/main.py — Puerto: 8001
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Auth API")
os.environ["PORT"] = "8001"

class UserCredentials(BaseModel):
    usuario: str
    password: str

# Base de datos en memoria para la práctica
_users_db = {"Ricardo": "12345"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-api"}

@app.post("/login")
def login(creds: UserCredentials):
    if creds.usuario in _users_db and _users_db[creds.usuario] == creds.password:
        return {"ok": True, "token": f"jwt_mock_{creds.usuario}"}
    raise HTTPException(status_code=401, detail="Credenciales inválidas")