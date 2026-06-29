import os
import shutil
import sqlite3
import asyncio  # ⏱️ Non-blocking async UI engine
import gradio as gr
import pandas as pd

# 🔌 Import the backend logic
import engine
import localization  # 🌐 Linked Macro-National Localization Module

# 🛡️ INTEGRATED SECURITY GUARDS: The 3-Layer Defense Matrix
from guard_limiter import check_upload_limit, RateLimitExceededError
from guard_validator import validate_file_spec
from guard_quarantine import inspect_binary_header

# 🧠 INTERNAL BRAIN WORKSPACE: Local Zero-DB Context Indexer
from rag_processor import LoreMapRAG

# ☁️ Hugging Face API Integration for Cloud Vault Routing
from huggingface_hub import HfApi

api = HfApi()
HF_TOKEN = os.environ.get("HF_TOKEN")

# Initialize the storage handshake, local database logs, and RAG Engine
engine.download_history_from_hub()
engine.init_db()
rag_engine = LoreMapRAG()

# 🌍 Your 5 Organized Stratagem Cloud Vaults
VAULTS = {
    ".png": "Narrative-engine-labs/stratagem-vault",
    ".jpg": "Narrative-engine-labs/stratagem-vault-jpg",
    ".jpeg": "Narrative-engine-labs/stratagem-vault-jpg",
    ".pdf": "Narrative-engine-labs/stratagem-vault-pdf",
    ".docx": "Narrative-engine-labs/stratagem-vault-docs",
    ".doc": "Narrative-engine-labs/stratagem-vault-docs",
    ".txt": "Narrative-engine-labs/stratagem-vault-text",
    ".md": "Narrative-engine-labs/stratagem-vault-text"
}

# Helper to format SQLite database rows into a professional file-explorer dataframe
def get_vault_dataframe(request: gr.Request):
    if not request or not request.username:
        return pd.DataFrame(columns=["File Name", "Compiled Timestamp", "Blueprint Snippet", "Size"])
    
    conn = sqlite3.connect(engine.DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, blueprint, manuscript FROM narrative_logs WHERE username = ? ORDER BY id DESC", (request.username,))
    rows = c.fetchall()
    conn.close()
    
    data = []
    for row in rows:
        log_id, timestamp, blueprint, manuscript = row
        clean_timestamp = timestamp.replace("-", "").replace(" ", "_").replace(":", "")
        file_name = f"artifact_{clean_timestamp}_{log_id}.txt"
        file_size = f"{round(len(manuscript.encode('utf-8')) / 1024, 2)} KB"
        
        data.append({
            "File Name": f"📄 {file_name}",
            "Compiled Timestamp": timestamp,
            "Blueprint Snippet": f"{blueprint[:40]}...",
            "Size": file_size
        })
        
    if not data:
        return pd.DataFrame([{"System Status": "No archived workspace containers detected in cloud vault."}])
        
    return pd.DataFrame(data)


# 🛡️ SECURE ASSET UPLOAD PIPELINE (WITH 5-WAY CLOUD ROUTING & RAG INDEXING)
def process_secure_upload(uploaded_file, request: gr.Request):
    """
    Chains all 3 local safety guards, then dynamically routes and mirrors 
    the verified asset out to its designated private Hugging Face cloud vault 
    while indexing the context locally into the LoreMapRAG matrix.
    """
    if uploaded_file is None:
        return "No temporary file allocation detected."
        
    user_token = request.username if (request and request.username) else "anonymous_node"
    temp_file_path = uploaded_file.name 
    base_name = os.path.basename(temp_file_path)
    _, ext = os.path.splitext(base_name.lower())
    
    try:
        # ---- GUARD 1: Rate Limiting ----
        check_upload_limit(user_token, max_uploads=5, window_seconds=60)
        
        # ---- GUARD 2: Size Constraints ----
        validate_file_spec(temp_file_path, max_mb=5.0)
        
        # ---- GUARD 3: Binary Quarantine Header Check ----
        inspect_binary_header(temp_file_path)
        
        # ---- ☁️ LAYER 4: MULTI-DATASET CLOUD ROUTER ----
        target_repo = VAULTS.get(ext, "Narrative-engine-labs/stratagem-vault-text")
        
        if not HF_TOKEN:
            print("❌ CONFIG ERROR: The 'HF_TOKEN' is missing from Space Secrets!")
            raise gr.Error("Backend Configuration Error: Cloud credentials missing.")
            
        print(f"🚀 Mirroring verified asset '{base_name}' to cloud vault pool -> {target_repo}")
        api.upload_file(
            path_or_fileobj=temp_file_path,
            path_in_repo=f"uploads/{base_name}",
            repo_id=target_repo,
            repo_type="dataset",
            token=HF_TOKEN
        )
        
        # ---- SECURE LOCAL PERSISTENCE STORAGE ----
        storage_dir = "./storage/user_assets"
        os.makedirs(storage_dir, exist_ok=True)
        final_destination = os.path.join(storage_dir, base_name)
        
        # Clone into local sandbox for engine accessibility
        shutil.copy(temp_file_path, final_destination)
        
        # ---- 🧠 LAYER 5: IN-MEMORY SLIDING WINDOW RAG CHUNKING ----
        rag_engine.load_and_chunk_file(final_destination)
        
        if hasattr(engine, 'register_attachment_in_db'):
            engine.register_attachment_in_db(user_token, final_destination)
            
        return f"✨ Asset verified, indexed to RAG, & deployed to pool: {target_repo.split('/')[-1]}/{base_name}"
        
    except RateLimitExceededError as e:
        raise gr.Error(str(e))
    except ValueError as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise gr.Error(f"Security Defusal: {str(e)}")
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise gr.Error(f"System Exception: Cloud cluster upload failed.")


# ⏱️ ASYNC PROGRESS TRACKER WRAPPER WITH INJECTED CONTEXT SCANNER
async def async_compilation_handler(api_token, outline, request: gr.Request, progress=gr.Progress()):
    """
    Intercepts the UI event thread to safely step through progress notifications,
    extracts target lore segments via RAG tracking vectors, and executes compilation.
    """
    if not api_token:
        return "⚠️ UI Safeguard Check: Please provide your Gemini Developer Token before executing.", "No telemetry logged."
    if not outline or len(outline.strip()) < 5:
        return "⚠️ UI Safeguard Check: Structure blueprint field is empty or insufficient.", "No telemetry logged."

    progress(0, desc="⚡ Connecting to Stratagem compilation hub...")
    await asyncio.sleep(0.3)
    
    progress(0.25, desc="🤖 Handshaking with Gemini 3.5 Flash engine...")
    
    # ---- 🧠 CONTEXT RECOVERY PIPELINE ----
    # Extract only the 3 most relevant context segments matching the active prompt outline
    injected_context = rag_engine.retrieve_context(outline, top_k=3)
    
    compilation_prompt = outline
    if injected_context:
        compilation_prompt = f"{injected_context}\n\n⚡ [SYSTEM COMPILATION BLUEPRINT]\n{outline}"
    
    await asyncio.sleep(0.3)
    progress(0.60, desc="📜 Compiling layout constraints & writing scene...")
    
    try:
        # Checks if engine logic is written as async or standard sync to prevent crashes
        if asyncio.iscoroutinefunction(engine.generate_story):
            result = await engine.generate_story(api_token, compilation_prompt, request)
        else:
            result = await asyncio.to_thread(engine.generate_story, api_token, compilation_prompt, request)
            
        progress(1.0, desc="✨ Scene compiled successfully!")
        return result  # 🌟 Dynamically passes the tuple: (manuscript_text, stats_summary)
        
    except Exception as e:
        progress(1.0, desc="❌ Operational anomaly detected.")
        return f"System Engine Exception: Handling thread failed. Details: {str(e)}", "Error compiling telemetry diagnostics."


# ==========================================
# 💎 PREMIUM DASHBOARD CSS STUDIO (OBSIDIAN THEME)
# ==========================================
CUSTOM_CSS = """
body, .gradio-container {
    background: radial-gradient(circle at top center, #0f111a 0%, #050608 100%) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: #f1f5f9 !important;
}
.gradio-container {
    max-width: 1400px !important;
    margin: 20px auto !important;
    padding: 24px !important;
    border: 1px solid #1e293b !important;
    border-radius: 16px !important;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.8) !important;
}
.header-container {
    border-bottom: 1px solid #1e293b !important;
    padding-bottom: 20px !important;
    margin-bottom: 24px !important;
    background: transparent !important;
}
.brand-title h1 {
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.03em !important;
    background: linear-gradient(135deg, #a78bfa 0%, #6366f1 50%, #38bdf8 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}
.tabs-navigation {
    border-bottom: 1px solid #1e293b !important;
    margin-bottom: 20px !important;
}
button.tab-nav {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #64748b !important;
    padding: 10px 16px !important;
    transition: all 0.2s ease !important;
}
button.tab-nav.selected {
    color: #a78bfa !important;
    border-bottom: 2px solid #a78bfa !important;
    background: transparent !important;
}
.workspace-card {
    background: #090d16 !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    padding: 24px !important;
}
textarea, input[type="text"], input[type="password"], .gr-dropdown {
    background: #04060a !important;
    border: 1px solid #1e293b !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}
textarea:focus, input:focus {
    border-color: #6366f1 !important;
}
.manuscript-canvas textarea {
    font-family: "Georgia", serif !important;
    font-size: 1.1rem !important;
    line-height: 1.8 !important;
    background: #0b0f19 !important;
    padding: 24px !important;
}
.action-btn {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
}
.action-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.5) !important;
}
.secondary-btn {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #cbd5e1 !important;
}
.secondary-btn:hover {
    background: #334155 !important;
}
"""

# ==========================================
# 🧱 INTERACTIVE DASHBOARD VIEW BUILDER
# ==========================================
with gr.Blocks(css=CUSTOM_CSS) as demo:
    
    # 🌟 Header Block Container
    with gr.Group(elem_classes="header-container"):
        gr.Markdown("# 🤖 CORE STRATAGEM WORKSPACE", elem_classes="brand-title")
        gr.Markdown("Enterprise-grade agentic manuscript compiler featuring decentralized history sync mechanics and zero-DB security parameters.")
    
    # 🗂️ Navigation Engine Tabs
    with gr.Tabs(elem_classes="tabs-navigation"):
        
        # TAB 1: INTERACTIVE COMPILER WORKSPACE
        with gr.Tab("🚀 Interactive AI Studio"):
            with gr.Row():
                with gr.Column(scale=4, elem_classes="workspace-card"):
                    gr.Markdown("### 🛠️ Operation Inputs")
                    api_input = gr.Textbox(
                        label="🔑 Gemini Developer Token", 
                        placeholder="Paste authorization token...", 
                        type="password"
                    )
                    outline_input = gr.Textbox(
                        label="📝 Structure Blueprint / Prompts", 
                        placeholder="Map structural constraints, story beats, outline components...", 
                        lines=10
                    )
                    
                    # 🛡️ INTEGRATED FILE ENTRY LAYOUT MODULES
                    file_uploader = gr.File(
                        label="📎 Attach Lore Map / Plot Binder (Max 5MB)",
                        file_types=[".png", ".jpg", ".jpeg", ".pdf", ".docx", ".doc", ".txt", ".md"],
                        file_count="single"
                    )
                    upload_status = gr.Textbox(
                        label="Asset Verification Status", 
                        placeholder="No external files staged in repository sandbox.", 
                        interactive=False
                    )
                    
                    # 🌐 NEW GLOBAL LOCALIZATION COMPONENT ENGINE
                    language_dropdown = gr.Dropdown(
                        choices=list(localization.TARGET_LANGUAGES.keys()),
                        value="Japanese (日本語)",
                        label="Global Translation Target Language"
                    )
                    translate_btn = gr.Button("🌐 EXECUTE REGIONAL TRANSLATION", elem_classes="action-btn secondary-btn")
                    
                    submit_btn = gr.Button("⚡ RUN COMPILATION QUEUE", variant="primary", elem_classes="action-btn")
                    
                with gr.Column(scale=6, elem_classes="workspace-card"):
                    gr.Markdown("### 📜 Output Console")
                    output_text = gr.Textbox(
                        label="Latest Compiled Manuscript", 
                        placeholder="System idle. Awaiting compilation pass execution...", 
                        lines=14,
                        elem_classes="manuscript-canvas"
                    )
                    
                    # 🌟 LAYER 4 TERMINAL ENGINE DIAGNOSTICS DISPLAY PANEL
                    telemetry_output = gr.Textbox(
                        label="🛰️ Layer 4 Narrative Telemetry Analytics", 
                        placeholder="Awaiting compilation sequence to pull real-time structural data summaries...", 
                        lines=6,
                        interactive=False
                    )
        
        # TAB 2: ADVANCED SECURE VAULT EXPLORER
        with gr.Tab("📁 Vault File Explorer"):
            with gr.Column(elem_classes="workspace-card"):
                gr.Markdown("### 🗄️ Private Cloud Storage Cloud Handshake")
                gr.Markdown("Browse all persistent narrative artifacts safely stored as an indexed ledger inside your private database container.")
                
                with gr.Row():
                    refresh_vault_btn = gr.Button("🔄 Scan Repository Storage", elem_classes="action-btn secondary-btn", scale=2)
                    history_dropdown = gr.Dropdown(label="Select File Anchor to Mount Content", choices=[], interactive=True, scale=8)
                
                vault_grid = gr.Dataframe(
                    headers=["File Name", "Compiled Timestamp", "Blueprint Snippet", "Size"],
                    datatype=["str", "str", "str", "str"],
                    row_count=5,
                    interactive=False,
                    label="Repository Index Manifest"
                )

    # ==========================================
    # 🎛️ EVENT HANDLERS & LINKAGES
    # ==========================================
    
    # ⏱️ Execution Pass Trigger linked to the updated Async Progress handler
    submit_btn.click(
        fn=async_compilation_handler, 
        inputs=[api_input, outline_input], 
        outputs=[output_text, telemetry_output],  # 🌟 Direct mapping to both workspace terminals
        show_progress="full"
    )
    
    # 🌐 Link the New Translation Pipeline Trigger
    translate_btn.click(
        fn=localization.translate_manuscript,
        inputs=[output_text, language_dropdown, api_input],
        outputs=[output_text]
    )
    
    # 🛡️ RUN SECURITY & ROUTER MATRIX UPON UPLOAD
    file_uploader.upload(
        fn=process_secure_upload,
        inputs=[file_uploader],
        outputs=upload_status
    )
    
    # Vault Repository Scanning Engine
    def trigger_vault_refresh(request: gr.Request):
        dropdown_update = engine.fetch_user_history_choices(request)
        dataframe_update = get_vault_dataframe(request)
        return dropdown_update, dataframe_update
        
    refresh_vault_btn.click(fn=trigger_vault_refresh, inputs=[], outputs=[history_dropdown, vault_grid])
    
    # Mounting a file context to the UI workspace fields
    def load_historical_file_to_studio(log_id):
        # 🌟 Unpacks all three outputs now stored in the database registry
        blueprint, manuscript, stats_summary = engine.restore_archived_session(log_id)
        return blueprint, manuscript, stats_summary
        
    history_dropdown.change(
        fn=load_historical_file_to_studio, 
        inputs=[history_dropdown], 
        outputs=[outline_input, output_text, telemetry_output]  # 🌟 Updates the diagnostics log on historical clicks
    )

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=10)
    demo.launch(
        auth=engine.verify_license_key, 
        auth_message="Welcome to Stratagem Workspace. Provide access token configurations.",
        css=CUSTOM_CSS
    )
    
