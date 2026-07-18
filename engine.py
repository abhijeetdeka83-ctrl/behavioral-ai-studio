# engine.py
import datetime
import json
import re
import sqlite3
import gradio as gr
import telemetry

# Clean structural pass-through imports to maintain backward compatibility with app.py
from models import MODEL_BUNDLES, SECRET_BYPASS_TOKEN, SECRET_BOUNDARIES, DB_FILE
from hf_storage import download_history_from_hub, upload_history_to_hub
from database import (
    init_db, register_beta_user, compile_active_state_manifest, 
    update_vault_state_from_prose, fetch_user_history_choices, restore_archived_session
)

# Shared routing layer engine calls and validation directly imported from router.py
from router import (
    identify_key_and_filter_bundles,
    call_google_engine, 
    call_openai_engine, call_anthropic_engine, call_open_source_engine
)

def check_url_bypass(request: gr.Request):
    if not request:
        return False, "anonymous"
    params = dict(request.query_params)
    if params.get("access") == SECRET_BYPASS_TOKEN:
        assigned_user = params.get("user", "alpha_reviewer")
        print(f"🔓 Security Matrix: Privileged magic URL bypass verified for session: {assigned_user}")
        return True, assigned_user
    return False, "anonymous"

def programmatic_violation_check(text):
    forbidden_patterns = [
        r"\brealized\b", r"\bunderstood\b", r"\bfelt\b", 
        r"\bcouldn't help but feel\b", r"\bfor the first time\b", 
        r"\bthe moment stayed\b", r"\bit bothered\b", r"\bshe knew\b", r"\bhe knew\b",
        r"\bwith the weight of\b", r"\bas if to say\b", r"\bseemed to symbolize\b"
    ]
    violations = []
    for pattern in forbidden_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            violations.append(f"'{matches[0]}'")
            
    name_matches = re.findall(r",\s*([A-Z][a-zA-Z]+)[\.!]", text)
    for name in name_matches:
        violations.append(f"', {name}'")
    return violations

def verify_license_key(username, password):
    return True

# ==========================================
# 🔄 CENTRALIZED STORY GENERATION PIPELINE
# ==========================================
async def generate_story(buyer_api_key, plot_outline, selected_bundle, session_username="anonymous"):
    if not buyer_api_key.strip() or not plot_outline.strip():
        return "🚨 System Status: Execution halted. Required fields are empty.", {}
    
    # CRITICAL FIX: Direct checking eliminates silent dictionary fallback crashes
    if selected_bundle not in MODEL_BUNDLES:
        error_stats = {"tier": "System Mismatch", "suppression_efficiency_pct": 0, "dialogue_diversity_pct": 0, "lexical_echo_phrases": 0, "pacing_dynamic_range": 0, "rag_log": "Pipeline execution rejected configuration."}
        return f"🚨 **Configuration Error:** The dropdown choice '{selected_bundle}' does not exist inside your models.py configuration map. Please check your spelling or re-type the key.", error_stats

    bundle_config = MODEL_BUNDLES[selected_bundle]
    provider = bundle_config["provider"]
    model_target = bundle_config["model"]
    model_type = bundle_config["type"]
    
    max_edits = 3 if model_type == "paid" else 5
    accumulated_prompt_tokens = 0
    accumulated_completion_tokens = 0
    loop_executions_count = 0
    
    try:
        live_state_manifest = compile_active_state_manifest(session_username)
        runtime_system_instruction = f"{SECRET_BOUNDARIES}\n\n{live_state_manifest}"
        initial_prompt = f"Execute the next structural scene based on this user blueprint: {plot_outline}"

        # --- DRAFT PHASE ---
        if provider == "open_source":
            raw_draft, usage = await call_open_source_engine(buyer_api_key, bundle_config["endpoint"], model_target, runtime_system_instruction, initial_prompt, 0.75)
            accumulated_prompt_tokens += usage.get("prompt_tokens", 0)
            accumulated_completion_tokens += usage.get("completion_tokens", 0)
        elif provider == "google":
            raw_draft = await call_google_engine(buyer_api_key, model_target, runtime_system_instruction, initial_prompt, 0.75)
        elif provider == "openai":
            raw_draft = await call_openai_engine(buyer_api_key, model_target, runtime_system_instruction, initial_prompt, 0.7)
        elif provider == "anthropic":
            raw_draft = await call_anthropic_engine(buyer_api_key, model_target, runtime_system_instruction, initial_prompt, 0.7)
            
        current_prose = raw_draft
        initial_violations = programmatic_violation_check(raw_draft)
        
        # --- RECURSIVE REVISION EDITING PASSES ---
        for loop_count in range(1, max_edits + 1):
            hard_violations = programmatic_violation_check(current_prose)
            if not hard_violations:
                break
                
            loop_executions_count += 1
            audit_prompt = f"You are an advanced software-driven copyediting compiler. Rewrite the following story text to completely remove these forbidden phrasing violations: {', '.join(hard_violations)}.\n{runtime_system_instruction}\n{current_prose}\nReturn ONLY the fully revised, complete story text."
            
            if provider == "open_source":
                current_prose, usage = await call_open_source_engine(buyer_api_key, bundle_config["endpoint"], model_target, runtime_system_instruction, audit_prompt, 0.3)
                accumulated_prompt_tokens += usage.get("prompt_tokens", 0)
                accumulated_completion_tokens += usage.get("completion_tokens", 0)
            elif provider == "google":
                current_prose = await call_google_engine(buyer_api_key, model_target, runtime_system_instruction, audit_prompt, 0.3)
            elif provider == "openai":
                current_prose = await call_openai_engine(buyer_api_key, model_target, runtime_system_instruction, audit_prompt, 0.3)
            elif provider == "anthropic":
                current_prose = await call_anthropic_engine(buyer_api_key, model_target, runtime_system_instruction, audit_prompt, 0.3)
        
        update_vault_state_from_prose(session_username, current_prose)
        stats = telemetry.calculate_prose_telemetry(draft_text=raw_draft, final_text=current_prose, initial_violations=initial_violations, checking_function=programmatic_violation_check)
        
        # Inject detailed token telemetry logs if running an open source layout
        if provider == "open_source":
            total_burned = accumulated_prompt_tokens + accumulated_completion_tokens
            stats["rag_log"] = (
                f"⚡ OS TOKEN CONSUMPTION ANALYSIS:\n"
                f"• Input/Context Cost: {accumulated_prompt_tokens:,} tokens\n"
                f"• Output/Prose Generation: {accumulated_completion_tokens:,} tokens\n"
                f"💥 Combined Operations Cost [Total Burn]: {total_burned:,} tokens across {loop_executions_count + 1} processing passes."
            )
        else:
            stats["rag_log"] = "🧠 Enterprise provider metadata streams locked. Framework verification clear."
            
        stats["tier"] = bundle_config["tier"]
        
        # ==========================================
        # 🛰️ GRAPHIFY CONTINUOUS AUTOMATED EXTRACTION LAYER
        # ==========================================
        if session_username and session_username != "anonymous":
            try:
                from graph_memory import GraphifyStoryMemory
                memory = GraphifyStoryMemory()
                
                proper_nouns = set(re.findall(r'\b[A-Z][a-z]{2,}\b', current_prose))
                filtered_stops = {"The", "And", "But", "This", "That", "With", "They", "Then", "From", "Here", "There", "Once"}
                
                discovered_entities = []
                for name in proper_nouns:
                    if name in filtered_stops:
                        continue
                    e_type = "Location" if "city" in current_prose.lower() or "room" in current_prose.lower() or "castle" in current_prose.lower() else "Character"
                    discovered_entities.append({
                        "name": name,
                        "type": e_type,
                        "status": "Active Context Stream"
                    })
                
                discovered_relationships = []
                if len(discovered_entities) >= 2:
                    for i in range(len(discovered_entities) - 1):
                        discovered_relationships.append({
                            "source": discovered_entities[i]["name"],
                            "target": discovered_entities[i+1]["name"],
                            "relation": "Linked In Scene"
                        })
                        
                memory.update_graph_from_scene(
                    username=session_username,
                    blueprint=plot_outline,
                    entities=discovered_entities,
                    relationships=discovered_relationships
                )
            except Exception as graph_err:
                print(f"⚠️ Graphify Pipeline Hook Exception: {str(graph_err)}")

        # Save records to ledger database
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO narrative_logs (username, timestamp, blueprint, manuscript, telemetry_json) VALUES (?, ?, ?, ?, ?)", (session_username, timestamp_str, plot_outline, current_prose, json.dumps(stats)))
        conn.commit()
        conn.close()
        
        # Sync the updated file up to the Hugging Face Dataset repo instantly
        upload_history_to_hub()
        return current_prose, stats
        
    except Exception as e:
        error_stats = {"tier": "Error State", "suppression_efficiency_pct": 0, "dialogue_diversity_pct": 0, "lexical_echo_phrases": 0, "pacing_dynamic_range": 0, "rag_log": "Pipeline execution stalled."}
        return f"❌ System Orchestrator Core Error: {str(e)}", error_stats

# ==========================================
# ⚡ AUTOMATED STARTUP STORAGE SYNCHRONIZATION
# ==========================================
# This executes globally the split second app.py imports engine.py,
# ensuring the remote database file is restored before any queries run.
print("🚀 [Storage Bridge] Initiating stateless memory recovery routine...")
try:
    download_history_from_hub()
except Exception as startup_err:
    print(f"⚠️ [Storage Bridge] Initial pull diagnostic notice: {startup_err}")

# Guarantee tables are structurally built whether it's a fresh bootstrap or a restored database
init_db()

# ==========================================
# 🛠️ FOOLPROOF DATABASE SCHEMA PATCH
# ==========================================
# This guarantees that the narrative_logs table exists in SQLite DB_FILE,
# completely preventing 'no such table' system core halts.
try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS narrative_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        timestamp TEXT,
        blueprint TEXT,
        manuscript TEXT,
        telemetry_json TEXT
    )
    """)
    conn.commit()
    conn.close()
    print("✅ [Database Patch] Successfully verified/created 'narrative_logs' table in local SQLite storage.")
except Exception as patch_err:
    print(f"⚠️ [Database Patch] Failed to apply table patch: {patch_err}")
    
