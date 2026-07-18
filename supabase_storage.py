# supabase_storage.py
import os
import mimetypes
from supabase import create_client, Client

# Pull credentials from Hugging Face Secrets
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
BUCKET_NAME = "workspace-media"

supabase: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"❌ [Supabase Storage Init Error]: {e}")

def upload_user_file(username: str, local_file_path: str) -> str:
    """
    Uploads files (JPG, PNG, PDF) straight to the Supabase Storage Bucket.
    Organizes assets into folders: 'username/filename'
    Returns the permanent public URL web link.
    """
    if not supabase:
        return "❌ Storage connection offline."
    
    if not local_file_path:
        return "❌ Invalid file path."
        
    try:
        filename = os.path.basename(local_file_path)
        # Clean username string to keep folder paths valid
        username_clean = username.strip().lower().replace("@", "_at_")
        storage_path = f"{username_clean}/{filename}"
        
        # Detect file type
        mime_type, _ = mimetypes.guess_type(local_file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        with open(local_file_path, 'rb') as f:
            file_data = f.read()

        # Upload to your public bucket folder
        supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": mime_type, "upsert": "true"}
        )
        
        # Generate the fast public access link instantly
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)
        return public_url

    except Exception as e:
        print(f"❌ Cloud Storage Upload Failure: {e}")
        return f"❌ Upload error: {str(e)}"
        
