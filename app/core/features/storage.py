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
    
def delete_file_from_supabase(file_url: str):
    if not file_url:
        return
    try:
        supabase = get_supabase_client()
        bucket_name = "vault_resources"
        
        split_token = f"/{bucket_name}/"
        if split_token in file_url:
            file_path = file_url.split(split_token)[-1]
            supabase.storage.from_(bucket_name).remove([file_path])
    except Exception as e:
        print(f"Storage deletion warning: {str(e)}")