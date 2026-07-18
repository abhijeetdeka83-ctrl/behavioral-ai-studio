# ui_handlers.py
import os
import shutil
import asyncio  
import requests 
import gradio as gr
import pandas as pd
import json

import engine
from database import supabase  # Inherit global Supabase client instance

from guard_limiter import check_upload_limit, RateLimitExceededError
from guard_validator import validate_file_spec
from guard_quarantine import inspect_binary_header

from rag_processor import SessionRAGManager
from supabase_storage import upload_user_file  # Import new cloud storage engine
from huggingface_hub import InferenceClient

HF_TOKEN = os.environ.get("HF_TOKEN")
rag_engine = SessionRAGManager()

def execute_gate_login(email, password):
    if not email or "@" not in email or "." not in email:
        raise gr.Error("🚨 Please enter a valid email configuration to initialize context allocations.")
    if not password or len(password.strip()) < 4:
        raise gr.Error("🚨 Please provide a valid security access key password.")
        
    clean_email = email.strip().lower()
    
    # Register or verify through cloud database layer
    total_tracked_users = engine.register_beta_user(clean_email)
    
    welcome_msg = f"🟢 **Status: Active** | Environment initialized securely for node: `{clean_email}`"
    stats_msg = f"📊 **Current Network Scale:** {total_tracked_users} total early software testers locked in."
    
    return (
        gr.update(visible=False), 
        gr.update(visible=True),  
        welcome_msg,              
        stats_msg,                
        clean_email               
    )

def build_v5_pacing_snippet(mode_name):
    if mode_name == "Slow_Burn":
        return """    <Mode name="Slow_Burn">
        <Priority_Order>
            1. Character Behavior
            2. Environment
            3. Relationships
            4. Plot Progression
        </Priority_Order>
        <Execution_Rules>
            - Allow conversations to wander naturally.
            - Permit scenes that exist only for atmosphere or character interaction.
            - Plot advancement is optional.
            - Environmental observation is encouraged.
            - Scene duration may exceed narrative efficiency.
        </Execution_Rules>
    </Mode>"""
    elif mode_name == "Balanced":
        return """    <Mode name="Balanced">
        <Priority_Order>
            1. Character Behavior
            2. Plot Progression
            3. Relationships
            4. Environment
        </Priority_Order>
        <Execution_Rules>
            - Every scene should advance either plot or relationships.
            - Conversations may drift briefly but naturally return.
            - Maintain moderate pacing.
            - Environmental detail supports the narrative without dominating it.
        </Execution_Rules>
    </Mode>"""
    else:
        return """    <Mode name="High_Momentum">
        <Priority_Order>
            1. Plot Progression
            2. Character Behavior
            3. Environment
            4. Atmosphere
        </Priority_Order>
        <Execution_Rules>
            - Compress routine actions.
            - Remove unnecessary pauses.
            - Dialogue should remain character-specific but more focused.
            - Environmental description should support immediate action.
            - Every scene should create measurable forward momentum.
        </Execution_Rules>
    </Mode>"""

def get_vault_dataframe(session_user):
    if not session_user or session_user == "anonymous" or not supabase:
        return pd.DataFrame(columns=["File Name", "Compiled Timestamp", "Blueprint Snippet", "Size"])
    
    try:
        # Pull records directly from Supabase cloud tables
        res = supabase.table("narrative_logs")\
            .select("id", "timestamp", "blueprint", "manuscript")\
            .eq("username", session_user)\
            .order("id", desc=True)\
            .execute()
        rows = res.data or []
    except Exception as e:
        print(f"❌ Failed to query vault dataframe: {e}")
        rows = []
    
    data = []
    for row in rows:
        log_id, timestamp = row["id"], row["timestamp"]
        blueprint, manuscript = row["blueprint"] or "", row["manuscript"] or ""
        
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

def process_secure_upload(uploaded_file, session_user):
    if uploaded_file is None:
        return "No temporary file allocation detected."
        
    user_token = session_user if session_user else "anonymous_node"
    temp_file_path = uploaded_file.name 
    base_name = os.path.basename(temp_file_path)
    
    try:
        check_upload_limit(user_token, max_uploads=5, window_seconds=60)
        validate_file_spec(temp_file_path, max_mb=5.0)
        inspect_binary_header(temp_file_path)
        
        # High speed asset deployment straight to Supabase Cloud Buckets
        cloud_url = upload_user_file(user_token, temp_file_path)
        if "❌" in cloud_url:
            raise gr.Error(cloud_url)
        
        # Keep local disk staging for downstream RAG vector calculations
        storage_dir = "./storage/user_assets"
        os.makedirs(storage_dir, exist_ok=True)
        final_destination = os.path.join(storage_dir, base_name)
        shutil.copy(temp_file_path, final_destination)
        
        _, rag_log = rag_engine.ingest_user_asset(user_token, final_destination)
        
        if hasattr(engine, 'register_attachment_in_db'):
            engine.register_attachment_in_db(user_token, final_destination)
            
        return f"✨ Asset verified, indexed to RAG, & deployed to bucket storage successfully!"
        
    except RateLimitExceededError as e:
        raise gr.Error(str(e))
    except ValueError as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise gr.Error(f"Security Defusal: {str(e)}")
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise gr.Error(f"System Exception: Cloud cluster upload rejected.")

# 🔄 UPDATED TO SEAMLESSLY MERGE VECTOR DICTIONARIES AND RAW TOKEN COUNTERS
async def async_compilation_handler(api_token, outline, bundle_name, pinned_context, 
                                    genre, pacing_mode, prose_density, dialogue_intensity, 
                                    description_level, world_visibility, emotional_opacity, 
                                    session_user="anonymous", progress=gr.Progress()):
    if not api_token or len(api_token.strip()) < 5:
        return "⚠️ UI Safeguard Check: Please provide a valid active workspace token or key string.", "Unknown", 0, 0, 0, 0, "No data profile logged."
    if not outline or len(outline.strip()) < 5:
        return "⚠️ UI Safeguard Check: Structure blueprint field is empty or insufficient.", "Unknown", 0, 0, 0, 0, "No data profile logged."

    progress(0, desc="⚡ Connecting to Stratagem compilation hub...")
    await asyncio.sleep(0.2)
    
    user_token = session_user if session_user else "anonymous_node"
    injected_context, rag_telemetry = rag_engine.retrieve_user_context(user_token, outline, top_k=3)
    
    pacing_xml_snippet = build_v5_pacing_snippet(pacing_mode)
    v5_profile_injection = f"""
<Pacing_Execution_Profile>
    [RUNTIME INJECTION]
    The pacing profile is selected dynamically before generation.
    The selected profile changes scene priorities without violating Character Integrity or Environmental Causality.
{pacing_xml_snippet}
</Pacing_Execution_Profile>

<Narrative_Profile>
    <Genre value="{genre}"/>
    <Pacing value="{pacing_mode}"/>
    <Prose_Density value="{prose_density}"/>
    <Dialogue_Intensity value="{dialogue_intensity}"/>
    <Description_Level value="{description_level}"/>
    <World_Visibility value="{world_visibility}"/>
    <Conflict_Frequency value="Medium"/>
    <Emotional_Opacity value="{emotional_opacity}"/>
</Narrative_Profile>
"""

    final_context_block = f"=== SYSTEM V5 EXECUTION SCHEMAS ===\n{v5_profile_injection}\n\n"
    if injected_context:
        final_context_block += f"=== RETRIEVED LORE MAPS ===\n{injected_context}\n\n"
    if pinned_context and pinned_context.strip():
        final_context_block += f"=== MANDATORY PINNED ENTITIES ===\n{pinned_context}\n\n"
        rag_telemetry = f"📌 Force-pinned manual profiles active.\n{rag_telemetry}"
        
    compilation_prompt = outline
    if final_context_block:
        compilation_prompt = f"{final_context_block}⚡ [SYSTEM COMPILATION BLUEPRINT]\n{outline}"
    
    progress(0.40, desc=f"🤖 Booting isolated workspace nodes via {bundle_name}...")
    
    try:
        if asyncio.iscoroutinefunction(engine.generate_story):
            manuscript_text, structured_stats = await engine.generate_story(api_token, compilation_prompt, bundle_name, user_token)
        else:
            manuscript_text, structured_stats = await asyncio.to_thread(engine.generate_story, api_token, compilation_prompt, bundle_name, user_token)
            
        progress(0.90, desc="📊 Mapping output telemetry metrics into layout interface view...")
        
        tier = structured_stats.get("tier", "Standard Quota")
        efficiency = float(structured_stats.get("suppression_efficiency_pct", 0))
        diversity = float(structured_stats.get("dialogue_diversity_pct", 0))
        echoes = int(structured_stats.get("lexical_echo_phrases", 0))
        pacing = float(structured_stats.get("pacing_dynamic_range", 0))
        
        # Merge vector matching metrics with runtime token logs cleanly
        complete_telemetry_summary = f"{rag_telemetry}\n\n{structured_stats.get('rag_log', '')}"
        
        progress(1.0, desc="✨ Scene compiled successfully via bundle strategy!")
        return manuscript_text, tier, efficiency, diversity, echoes, pacing, complete_telemetry_summary
        
    except Exception as e:
        progress(1.0, desc="❌ Operational anomaly detected.")
        return f"System Engine Exception: Handling thread failed. Details: {str(e)}", "Error", 0, 0, 0, 0, "Error compiling telemetry diagnostics."

def generate_cover_art(image_prompt, design_style):
    if not HF_TOKEN:
        raise gr.Error("Cloud Sandbox Alert: HF_TOKEN environment variable is missing.")
    if not image_prompt or len(image_prompt.strip()) < 3:
        return None
        
    try:
        client = InferenceClient(token=HF_TOKEN)
        structured_prompt = f"Book cover illustration art, {image_prompt}, detailed composition, masterpiece studio rendering, {design_style} aesthetic"
        image = client.text_to_image(prompt=structured_prompt, model="black-forest-labs/FLUX.1-schnell")
        return image
    except Exception as e:
        raise gr.Error(f"Illustration Cluster Error: {str(e)}")

def trigger_vault_refresh(session_user):
    dropdown_update = engine.fetch_user_history_choices(session_user)
    dataframe_update = get_vault_dataframe(session_user)
    return dropdown_update, dataframe_update

def load_historical_file_to_studio(log_id):
    blueprint, manuscript, stats_summary, structured_data = engine.restore_archived_session(log_id)
    return (
        blueprint, 
        manuscript, 
        structured_data.get("tier", "Historical Workspace Archive"),
        float(structured_data.get("suppression_efficiency_pct", 0)),
        float(structured_data.get("dialogue_diversity_pct", 0)),
        int(structured_data.get("lexical_echo_phrases", 0)),
        float(structured_data.get("pacing_dynamic_range", 0)),
        f"Loaded historical log sequence. Content mounted successfully.\n\n{structured_data.get('rag_log', '')}"
    )
    
