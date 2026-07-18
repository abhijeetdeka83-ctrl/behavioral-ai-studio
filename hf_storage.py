import os
import shutil
from huggingface_hub import hf_hub_download, HfApi

# ==========================================
# ⚙️ CONFIGURATION & HARDCODED REPOS
# ==========================================
HF_TOKEN = os.getenv("HF_TOKEN")
DATABASE_FILENAME = "stratagem.db"
LOCAL_VAULT_DIR = "vault_media"

# Ensure local asset caching folder exists
os.makedirs(LOCAL_VAULT_DIR, exist_ok=True)
api = HfApi(token=HF_TOKEN)

# ==========================================
# 🗺️ AUTOMATED EXTENSION ROUTING MATRIX
# ==========================================
DATASET_ROUTER = {
    # Image types and look-alikes
    "jpg": "Narrative-engine-labs/stratagem-vault-jpg",
    "jpeg": "Narrative-engine-labs/stratagem-vault-jpg",
    "png": "Narrative-engine-labs/stratagem-vault-jpg",
    "webp": "Narrative-engine-labs/stratagem-vault-jpg",
    "bmp": "Narrative-engine-labs/stratagem-vault-jpg",
    
    # Plain text and data frameworks
    "txt": "Narrative-engine-labs/stratagem-vault-text",
    "json": "Narrative-engine-labs/stratagem-vault-text",
    "csv": "Narrative-engine-labs/stratagem-vault-text",
    "md": "Narrative-engine-labs/stratagem-vault-text",
    
    # Rich Document standard formats
    "doc": "Narrative-engine-labs/stratagem-vault-docs",
    "docx": "Narrative-engine-labs/stratagem-vault-docs",
    "rtf": "Narrative-engine-labs/stratagem-vault-docs",
    "odt": "Narrative-engine-labs/stratagem-vault-docs",
    
    # Portable Document Formats
    "pdf": "Narrative-engine-labs/stratagem-vault-pdf",
    
    # Legacy Narrative Data Vault
    "legacy": "Narrative-engine-labs/stratagem-vault-legacy"
}

# The catch-all default dataset repository for core databases (.db) and unhandled items
DEFAULT_DATASET = "Narrative-engine-labs/stratagem-vault"


def get_target_repo(filename):
    """
    Looks at a file extension and determines which dedicated dataset it belongs to.
    """
    ext = filename.lower().split('.')[-1]
    return DATASET_ROUTER.get(ext, DEFAULT_DATASET)

# ==========================================
# 🗃️ PRIMARY ledgers SYNC (stratagem.db)
# ==========================================
def download_history_from_hub():
    """Downloads the core SQLite database file from the primary default dataset."""
    if not HF_TOKEN:
        print("⚠️ HF_TOKEN missing. Operating in local ephemeral runtime mode.")
        return

    try:
        print(f"🔄 Pulling central structural ledger from: {DEFAULT_DATASET}...")
        downloaded_path = hf_hub_download(
            repo_id=DEFAULT_DATASET,
            filename=DATABASE_FILENAME,
            repo_type="dataset",
            token=HF_TOKEN
        )
        if os.path.exists(downloaded_path):
            shutil.copy(downloaded_path, DATABASE_FILENAME)
            print("✅ Main workspace database loaded completely!")
    except Exception as e:
        if "404" in str(e):
            print("🆕 Primary database file not found on remote. Bootstrapping new repository architecture.")
        else:
            print(f"❌ Database initialization sequence failed: {e}")


def upload_history_to_hub():
    """Uploads the core SQLite state file back to the primary default dataset."""
    if not HF_TOKEN or not os.path.exists(DATABASE_FILENAME):
        return

    try:
        api.upload_file(
            path_or_fileobj=DATABASE_FILENAME,
            path_in_repo=DATABASE_FILENAME,
            repo_id=DEFAULT_DATASET,
            repo_type="dataset"
        )
        print("✅ Main state database backed up safely to stratagem-vault!")
    except Exception as e:
        print(f"❌ Core database storage sync failed: {e}")

# ==========================================
# 🖼️ SMART MULTI-DATASET ASSET UPLOADER
# ==========================================
def upload_vault_asset_to_hub(local_file_path):
    """
    Dynamically reads any file's format type, routes it to the specific matched 
    dataset repository, and backs it up on the Hugging Face Hub.
    """
    if not HF_TOKEN:
        print("⚠️ Warning: Token unverified. Asset tracking limited to local system.")
        return None

    filename = os.path.basename(local_file_path)
    target_repo = get_target_repo(filename)
    
    try:
        print(f"📦 Routing '{filename}' automatically to ➡️ {target_repo}...")
        
        # Keep a tracking backup copy inside the local workspace media cache folder
        cached_path = os.path.join(LOCAL_VAULT_DIR, filename)
        if local_file_path != cached_path:
            shutil.copy(local_file_path, cached_path)

        # Upload to the root of the targeted dataset repo matrix
        api.upload_file(
            path_or_fileobj=cached_path,
            path_in_repo=filename,
            repo_id=target_repo,
            repo_type="dataset"
        )
        print(f"✅ Secure Vault Sync completed for '{filename}'!")
        return cached_path
        
    except Exception as e:
        print(f"❌ Dynamic Asset Router failed for file {filename}: {e}")
        return None

# ==========================================
# 🔄 GLOBAL RECOVERY BOOT SYNC
# ==========================================
def download_all_vault_assets():
    """
    Iterates through all 5 dataset pools on startup, pulling down all text, 
    images, pdfs, and documents to fill the File Explorer tabs correctly.
    """
    if not HF_TOKEN:
        return

    all_repos = set(list(DATASET_ROUTER.values()) + [DEFAULT_DATASET])
    print(f"🔄 Executing global sync across {len(all_repos)} secure dataset storage cells...")
    
    for repo in all_repos:
        try:
            repo_files = api.list_repo_files(repo_id=repo, repo_type="dataset")
            for file_in_repo in repo_files:
                # Bypass tracking internal configuration files
                if file_in_repo.startswith(".") or file_in_repo == DATABASE_FILENAME:
                    continue
                    
                local_dest = os.path.join(LOCAL_VAULT_DIR, file_in_repo)
                if not os.path.exists(local_dest):
                    downloaded_file = hf_hub_download(
                        repo_id=repo,
                        filename=file_in_repo,
                        repo_type="dataset",
                        token=HF_TOKEN
                    )
                    shutil.copy(downloaded_file, local_dest)
        except Exception as e:
            print(f"⚠️ Notice: Skipping asset scanning sector for [{repo}]: {e}")
            
    print("✅ System Core asset synchronization matrix is fully online.")
