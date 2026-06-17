# Pérez Hernández Ricardo — Práctica 8
# media-api/main.py — Puerto: 8002
import os
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI(title="Media API")
os.environ["PORT"] = "8002"

class MediaResponse(BaseModel):
    filename: str
    storage_url: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "media-api"}

@app.post("/upload/image", response_model=MediaResponse)
async def upload_image(file: UploadFile = File(...)):
    # Lógica estructurada para delegar el blob a Supabase Storage
    # supabase.storage.from_('chat-images').upload(file.filename, file.file)
    mock_supabase_url = f"https://kdfj...supabase.co/storage/v1/object/public/chat-images/{file.filename}"
    
    return MediaResponse(
        filename=file.filename,
        storage_url=mock_supabase_url
    )