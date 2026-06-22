import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="Media API")

# 1. CORS es obligatorio para que el frontend pueda conectar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Inicializar Supabase usando variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class MediaResponse(BaseModel):
    filename: str
    storage_url: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "media-api"}

@app.post("/upload/image", response_model=MediaResponse)
async def upload_image(file: UploadFile = File(...)):
    # Leer el contenido del archivo
    contents = await file.read()
    
    # Subir a Supabase
    # Asegúrate de que el bucket se llame 'chat-images'
    supabase.storage.from_("chat-images").upload(
        path=file.filename,
        file=contents,
        file_options={"content-type": file.content_type, "upsert": "true"}
    )
    
    # Construir la URL pública real
    url_publica = f"{SUPABASE_URL}/storage/v1/object/public/chat-images/{file.filename}"
    
    return MediaResponse(
        filename=file.filename,
        storage_url=url_publica
    )
