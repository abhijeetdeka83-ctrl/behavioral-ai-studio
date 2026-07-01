# app.py
import os
import shutil
import sqlite3
import asyncio  # ⏱️ Non-blocking async UI engine
import requests # 🌐 Network pinger for live token checking
import gradio as gr
import pandas as pd
import json

# 🔌 Import the backend logic
import engine
import localization  

# 🛡️ INTEGRATED SECURITY GUARDS
from guard_limiter import check_upload_limit, RateLimitExceededError
from guard_validator import validate_file_spec
from guard_quarantine import inspect_binary_header

# 🧠 INTERNAL BRAIN WORKSPACE
from rag_processor import SessionRAGManager

# ☁️ Hugging Face API Integration
from huggingface_hub import HfApi

api = HfApi()
HF_TOKEN = os.environ.get("HF_TOKEN")

# Initialize synchronization frames and frameworks
engine.download_history_from_hub()
engine.init_db()
rag_engine = SessionRAGManager()

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

# 🔍 REAL-TIME EVENT-DRIVEN TOKEN CHECKER
def verify_gemini_token_status(api_token):
    if not api_token or len(api_token.strip()) < 10:
        return "txt", "⚪ **Status:** Missing token string. Staging window is currently idle."
        
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_token}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return "🟢 **Status: Active & Ready** | Key signature validated. Quota headroom functional."
        elif response.status_code == 429:
            return "🟡 **Status: Exhausted / Rate-Limited** | Resource threshold pacing throttled (429)."
        elif response.status_code in [400, 403]:
            return "🔴 **Status: Invalid Key Configuration** | Authentication rejected by cluster."
        else:
            return f"orange", f"硬 **Status: Code {response.status_code}** | Context indicator check failure."
    except requests.exceptions.RequestException:
        return "❌ **Status: Network Timeout** | Local network failed to handshake with validation cluster."

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

def process_secure_upload(uploaded_file, request: gr.Request):
    if uploaded_file is None:
        return "No temporary file allocation detected."
        
    user_token = request.username if (request and request.username) else "anonymous_node"
    temp_file_path = uploaded_file.name 
    base_name = os.path.basename(temp_file_path)
    _, ext = os.path.splitext(base_name.lower())
    
    try:
        check_upload_limit(user_token, max_uploads=5, window_seconds=60)
        validate_file_spec(temp_file_path, max_mb=5.0)
        inspect_binary_header(temp_file_path)
        
        target_repo = VAULTS.get(ext, "Narrative-engine-labs/stratagem-vault-text")
        
        if not HF_TOKEN:
            raise gr.Error("Backend Configuration Error: Cloud credentials missing.")
            
        api.upload_file(
            path_or_fileobj=temp_file_path,
            path_in_repo=f"uploads/{base_name}",
            repo_id=target_repo,
            repo_type="dataset",
            token=HF_TOKEN
        )
        
        storage_dir = "./storage/user_assets"
        os.makedirs(storage_dir, exist_ok=True)
        final_destination = os.path.join(storage_dir, base_name)
        shutil.copy(temp_file_path, final_destination)
        
        _, rag_log = rag_engine.ingest_user_asset(user_token, final_destination)
        
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

# ⏱️ ASYNC HANDLER INTERACTIVELY PACKS DASHBOARD KPIs
async def async_compilation_handler(api_token, outline, bundle_name, request: gr.Progress, progress=gr.Progress()):
    if not api_token:
        return "⚠️ UI Safeguard Check: Please provide your Gemini Developer Token before executing.", "Unknown", 0, 0, 0, 0, "No data profile logged."
    if not outline or len(outline.strip()) < 5:
        return "⚠️ UI Safeguard Check: Structure blueprint field is empty or insufficient.", "Unknown", 0, 0, 0, 0, "No data profile logged."

    progress(0, desc="⚡ Connecting to Stratagem compilation hub...")
    await asyncio.sleep(0.2)
    
    user_token = request.username if (request and request.username) else "anonymous_node"
    injected_context, rag_telemetry = rag_engine.retrieve_user_context(user_token, outline, top_k=3)
    
    compilation_prompt = outline
    if injected_context:
        compilation_prompt = f"{injected_context}\n\n⚡ [SYSTEM COMPILATION BLUEPRINT]\n{outline}"
    
    progress(0.40, desc=f"🤖 Booting isolated workspace nodes via {bundle_name}...")
    
    try:
        if asyncio.iscoroutinefunction(engine.generate_story):
            manuscript_text, structured_stats = await engine.generate_story(api_token, compilation_prompt, bundle_name, request)
        else:
            manuscript_text, structured_stats = await asyncio.to_thread(engine.generate_story, api_token, compilation_prompt, bundle_name, request)
            
        progress(0.90, desc="📊 Mapping output telemetry metrics into layout interface view...")
        
        # Pull safe data frames out of structured dictionary output
        tier = structured_stats.get("tier", "Standard Quota")
        efficiency = float(structured_stats.get("suppression_efficiency_pct", 0))
        diversity = float(structured_stats.get("dialogue_diversity_pct", 0))
        echoes = int(structured_stats.get("lexical_echo_phrases", 0))
        pacing = float(structured_stats.get("pacing_dynamic_range", 0))
        
        progress(1.0, desc="✨ Scene compiled successfully via bundle strategy!")
        return manuscript_text, tier, efficiency, diversity, echoes, pacing, rag_telemetry
        
    except Exception as e:
        progress(1.0, desc="❌ Operational anomaly detected.")
        return f"System Engine Exception: Handling thread failed. Details: {str(e)}", "Error", 0, 0, 0, 0, "Error compiling telemetry diagnostics."

# ==========================================
# 💎 PREMIUM OBSIDIAN CSS THEME STUDIO
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
.status-badge {
    background: #04060a !important;
    border: 1px solid #1e293b !important;
    padding: 10px 14px !important;
    border-radius: 6px !important;
    font-size: 0.88rem !important;
    display: block;
}
.kpi-container {
    background: #04060a !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    padding: 12px !important;
}
"""

# ==========================================
# 🧱 INTERACTIVE DASHBOARD VIEW BUILDER
# ==========================================
with gr.Blocks(css=CUSTOM_CSS) as demo:
    
    with gr.Group(elem_classes="header-container"):
        gr.Markdown("# 🤖 CORE STRATAGEM WORKSPACE", elem_classes="brand-title")
        gr.Markdown("Enterprise-grade agentic manuscript compiler featuring decentralized history sync mechanics and zero-DB security parameters.")
    
    with gr.Tabs(elem_classes="tabs-navigation"):
        
        # TAB 1: INTERACTIVE COMPILER WORKSPACE
        with gr.Tab("🚀 Interactive AI Studio"):
            with gr.Row():
                with gr.Column(scale=4, elem_classes="workspace-card"):
                    gr.Markdown("### 🛠️ Operation Inputs")
                    
                    api_input = gr.Textbox(
                        label="🔑 Gemini Developer Token", 
                        placeholder="Paste authorization token configuration here...", 
                        type="password"
                    )
                    
                    key_status_box = gr.Markdown("臨 **Status:** Staging window is currently idle.", elem_classes="status-badge")
                    
                    bundle_dropdown = gr.Dropdown(
                        choices=list(engine.MODEL_BUNDLES.keys()),
                        value=list(engine.MODEL_BUNDLES.keys())[1], 
                        label="📦 Select AI Engine Deployment Bundle"
                    )
                    
                    outline_input = gr.Textbox(
                        label="📝 Structure Blueprint / Prompts", 
                        placeholder="Map structural constraints, story beats, outline components...", 
                        lines=10
                    )
                    
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
                    
                    # 🛰️ INTERACTIVE LIVE KPI METRICS PANEL
                    gr.Markdown("### 🛰️ Layer 4 Narrative Telemetry Analytics Dashboard")
                    with gr.Group(elem_classes="kpi-container"):
                        with gr.Row():
                            ui_tier_badge = gr.Textbox(label="🏷️ Active Quota Footprint Tier", value="N/A", interactive=False)
                            ui_echo_badge = gr.Number(label="🔄 Lexical Echo Phrases Caught", value=0, interactive=False)
                        with gr.Row():
                            ui_efficiency_slider = gr.Slider(label="📈 Forbidden Phrase Suppression Efficiency", minimum=0, maximum=100, value=0, interactive=False)
                            ui_diversity_slider = gr.Slider(label="🎭 Dialogue Diversity Score", minimum=0, maximum=100, value=0, interactive=False)
                        with gr.Row():
                            ui_pacing_badge = gr.Number(label="⏳ Pacing Dynamic Range (Sentence StdDev Words)", value=0, interactive=False)
                        
                        ui_rag_telemetry = gr.Textbox(label="🧠 Active Knowledge Retrieval Vector Logs", placeholder="No asset data pulled into current execution stack.", lines=3, interactive=False)
        
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
    # 🎛️ AUTOMATED EVENT HANDLERS & LINKAGES
    # ==========================================
    
    # ⚡ AUTOMATION HOOKS: Auto-runs verification on paste (.change) or exit (.blur)
    api_input.change(fn=verify_gemini_token_status, inputs=[api_input], outputs=[key_status_box])
    api_input.blur(fn=verify_gemini_token_status, inputs=[api_input], outputs=[key_status_box])
    
    # Connect compile buttons to unpack results interactively across components
    submit_btn.click(
        fn=async_compilation_handler, 
        inputs=[api_input, outline_input, bundle_dropdown], 
        outputs=[output_text, ui_tier_badge, ui_efficiency_slider, ui_diversity_slider, ui_echo_badge, ui_pacing_badge, ui_rag_telemetry],  
        show_progress="full"
    )
    
    translate_btn.click(
        fn=localization.translate_manuscript,
        inputs=[output_text, language_dropdown, api_input],
        outputs=[output_text]
    )
    
    file_uploader.upload(
        fn=process_secure_upload,
        inputs=[file_uploader],
        outputs=upload_status
    )
    
    def trigger_vault_refresh(request: gr.Request):
        dropdown_update = engine.fetch_user_history_choices(request)
        dataframe_update = get_vault_dataframe(request)
        return dropdown_update, dataframe_update
        
    refresh_vault_btn.click(fn=trigger_vault_refresh, inputs=[], outputs=[history_dropdown, vault_grid])
    
    # 📂 INTERACTIVE WORKSPACE INGESTION PIPELINE FOR HISTORY SELECTOR
    def load_historical_file_to_studio(log_id):
        blueprint, manuscript, stats_summary, structured_data = engine.restore_archived_session(log_id)
        
        # Pull values out to mount to dashboard dynamically
        return (
            blueprint, 
            manuscript, 
            structured_data.get("tier", "Historical Workspace Archive"),
            float(structured_data.get("suppression_efficiency_pct", 0)),
            float(structured_data.get("dialogue_diversity_pct", 0)),
            int(structured_data.get("lexical_echo_phrases", 0)),
            float(structured_data.get("pacing_dynamic_range", 0)),
            "Loaded historical log sequence. System operational context successfully mounted."
        )
        
    history_dropdown.change(
        fn=load_historical_file_to_studio, 
        inputs=[history_dropdown], 
        outputs=[outline_input, output_text, ui_tier_badge, ui_efficiency_slider, ui_diversity_slider, ui_echo_badge, ui_pacing_badge, ui_rag_telemetry]  
    )

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=10)
    demo.launch(
        auth=engine.verify_license_key, 
        auth_message="Welcome to Stratagem Workspace. Provide access token configurations.",
        css=CUSTOM_CSS
)
