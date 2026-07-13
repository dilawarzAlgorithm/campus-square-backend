import os
import uuid
from supabase import create_client, Client
from fastapi import HTTPException

from app.core.config.config import settings

def get_supabase_client():
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Supabase credentials are not configured in the .env file.")
    return create_client(settings.supabase_url, settings.supabase_key)

def upload_file_to_supabase(file_bytes: bytes, original_filename: str, content_type: str):
    try:
        supabase = get_supabase_client()
        bucket_name = "vault_resources" 

        ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"

        supabase.storage.from_(bucket_name).upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": content_type}
        )

        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        return public_url
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")