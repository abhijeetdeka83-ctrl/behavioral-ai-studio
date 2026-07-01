# engine.py
import os
import datetime
import hashlib
import json
import re
import asyncio
import sqlite3
import gradio as gr
from google import genai
from google.genai import types
from huggingface_hub import HfApi, hf_hub_download
import telemetry  

DB_FILE = "narrative_history.db"
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_DATASET_ID = os.environ.get("HF_DATASET_ID")
SECRET_SALT = os.environ.get("SECRET_BOUNDARIES_SALT", "super_secret_fallback_phrase_99")
SECRET_BOUNDARIES = os.environ.get("STRUCTURAL_BOUNDARIES", "Error: Prompt constraints missing.")
SECRET_BYPASS_TOKEN = os.environ.get("URL_BYPASS_TOKEN", "alpha_access_2026")

MODEL_BUNDLES = {
    "1. Budget Echo Loop (Flash Lite Matrix)": {
        "draft": "gemini-3.1-flash-lite",
        "refine": "gemini-3.1-flash-lite",
        "tier": "🟢 Ultra-Low Quota Spend"
    },
    "2. Frontier Agent Baseline (Native 3.5 Speed)": {
        "draft": "gemini-3.5-flash",
        "refine": "gemini-3.5-flash",
        "tier": "🟢 Low Quota Spend"
    },
    "3. Stylist's Vault (Pro Draft + Flash Check)": {
        "draft": "gemini-3.1-pro-preview",
        "refine": "gemini-3.5-flash",
        "tier": "🟡 Medium Quota Spend"
    },
    "4. Heavy Editorial Audit (Flash Draft + Pro Check)": {
        "draft": "gemini-3.5-flash",
        "refine": "gemini-3.1-pro-preview",
        "tier": "🟠 High Quota Spend"
    },
    "5. The Literary Masterpiece (Pure Pro Execution)": {
        "draft": "gemini-3.1-pro-preview",
        "refine": "gemini-3.1-pro-preview",
        "tier": "🔴 Maximum Quota Spend"
    },
    "6. Logic Sentinel (Quick Draft + Deep Analytics)": {
        "draft": "gemini-2.5-flash",
        "refine": "gemini-3.1-pro-preview",
        "tier": "🟡 Medium Quota Spend"
    },
    "7. Dialogue Smooth-Talker (Agentic Flow Layout)": {
        "draft": "gemini-3.5-flash",
        "refine": "gemini-3.1-flash-lite",
        "tier": "🟢 Low-Medium Quota Spend"
    },
    "8. Legacy Stable Anchor (Classic 2.5 Engine)": {
        "draft": "gemini-2.5-pro",
        "refine": "gemini-2.5-pro",
        "tier": "🔴 High Quota Spend"
    },
    "9. The Layered Build (Gradual Revision Stack)": {
        "draft": "gemini-3.1-flash-lite",
        "refine": "gemini-3.5-flash",
        "tier": "🟡 Medium Quota Spend"
    },
    "10. Experimental Loop (2026 Sandbox Hybrid)": {
        "draft": "gemini-3.5-flash",
        "refine": "gemini-3.1-pro-preview",
        "tier": "🟠 High Quota Spend"
    }
}

def download_history_from_hub():
    if not HF_TOKEN or not HF_DATASET_ID:
        print("⚠️ HF Sync: Configuration environment secrets missing. Operating in local ephemeral mode.")
        return
    try:
        print(f"🚀 HF Sync: Connecting to dataset repo '{HF_DATASET_ID}' to sync data ledger...")
        hf_hub_download(repo_id=HF_DATASET_ID, filename=DB_FILE, repo_type="dataset", token=HF_TOKEN, local_dir=".")
        print("✅ HF Sync: Data ledger successfully cloned into active runtime instance.")
    except Exception as e:
        print(f"ℹ️ HF Sync: Ledger file not found or initializing fresh workspace structure ({e}).")

def upload_history_to_hub():
    if not HF_TOKEN or not HF_DATASET_ID:
        return
    try:
        api = HfApi()
        api.upload_file(path_or_fileobj=DB_FILE, path_in_repo=DB_FILE, repo_id=HF_DATASET_ID, repo_type="dataset", token=HF_TOKEN)
        print("💾 HF Sync: SQLite delta changes committed securely to cloud dataset container.")
    except Exception as e:
        print(f"🚨 HF Sync: Backup process failed to verify pipeline stream: {e}")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS narrative_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            blueprint TEXT,
            manuscript TEXT
        )
    ''')
    try:
        c.execute("ALTER TABLE narrative_logs ADD COLUMN telemetry_json TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    c.execute('''
        CREATE TABLE IF NOT EXISTS vault_state_registry (
            username TEXT PRIMARY KEY,
            state_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def check_url_bypass(request: gr.Request):
    """Inspects query parameters to check for secure URL-based login bypasses."""
    if not request:
        return False, "anonymous"
    params = dict(request.query_params)
    if params.get("access") == SECRET_BYPASS_TOKEN:
        assigned_user = params.get("user", "alpha_reviewer")
        print(f"🔓 Security Matrix: Privileged magic URL bypass verified for user session: {assigned_user}")
        return True, assigned_user
    return False, "anonymous"

def compile_active_state_manifest(username: str) -> str:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT state_json FROM vault_state_registry WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        state = {
            "environment_degradation": ["No severe structural anomalies logged"],
            "character_knowledge_flags": {}
        }
    else:
        state = json.loads(row[0])
        
    char_flags = state.get('character_knowledge_flags', {})
    char_lines = []
    
    if not char_flags:
        char_lines.append("No explicit character knowledge baselines tracked yet.")
    else:
        for char_name, flags in char_flags.items():
            char_lines.append(f"{char_name} Knowledge Base: {', '.join(flags)}")
            
    return f"""
    <LAYER_2_ACTIVE_STATE>
    Environmental Degradation Tracking: {', '.join(state.get('environment_degradation', ['No anomalies logged']))}
    {"\n    ".join(char_lines)}
    </LAYER_2_ACTIVE_STATE>
    """

def update_vault_state_from_prose(username: str, script_text: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT state_json FROM vault_state_registry WHERE username = ?", (username,))
    row = c.fetchone()
    
    state = json.loads(row[0]) if row else {
        "environment_degradation": [],
        "character_knowledge_flags": {}
    }
    
    if re.search(r"\b(broke|shattered|tore|spilled|leaked|sheared|failed|cracked|ruined|smashed)\b", script_text, re.IGNORECASE):
        timestamp_now = datetime.datetime.now().strftime("%H:%M")
        state["environment_degradation"].append(f"Material structural decay trace verified at {timestamp_now}")
        
    state["environment_degradation"] = list(set(state["environment_degradation"]))[-4:]
    
    c.execute("INSERT OR REPLACE INTO vault_state_registry (username, state_json) VALUES (?, ?)", (username, json.dumps(state)))
    conn.commit()
    conn.close()

def programmatic_violation_check(text):
    forbidden_patterns_case_insensitive = [
        r"\brealized\b", r"\bunderstood\b", r"\bfelt\b", 
        r"\bcouldn't help but feel\b", r"\bfor the first time\b", 
        r"\bthe moment stayed\b", r"\bit bothered\b", r"\bshe knew\b", r"\bhe knew\b",
        r"\bwith the weight of\b", r"\bas if to say\b", r"\bseemed to symbolize\b"
    ]
    violations = []
    
    # Process general lexical style violations
    for pattern in forbidden_patterns_case_insensitive:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            violations.append(f"'{matches[0]}'")
            
    # Cast-agnostic syntax validation (catches improper punctuation breaks after any capitalized character name)
    name_pattern = r",\s*([A-Z][a-zA-Z]+)[\.!]"
    name_matches = re.findall(name_pattern, text)
    for name in name_matches:
        violations.append(f"', {name}'")
        
    return violations

async def generate_story(buyer_api_key, plot_outline, selected_bundle, session_username="anonymous"):
    if not buyer_api_key.strip() or not plot_outline.strip():
        return "🚨 System Status: Execution halted. Required fields are empty.", {}
    
    bundle_config = MODEL_BUNDLES.get(selected_bundle, MODEL_BUNDLES["2. Frontier Agent Baseline (Native 3.5 Speed)"])
    draft_model_target = bundle_config["draft"]
    refine_model_target = bundle_config["refine"]
        
    try:
        client = genai.Client(api_key=buyer_api_key)
        
        async def execute_with_retry_async(model, contents, config, max_retries=3):
            for attempt in range(max_retries):
                try:
                    return await client.aio.models.generate_content(model=model, contents=contents, config=config)
                except Exception as e:
                    if "503" in str(e) or "429" in str(e):
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1.5 * (attempt + 1))  
                            continue
                    raise e

        live_state_manifest = compile_active_state_manifest(session_username)
        runtime_system_instruction = f"{SECRET_BOUNDARIES}\n\n{live_state_manifest}"

        response = await execute_with_retry_async(
            model=draft_model_target,
            contents=f"Execute the next structural scene based on this user blueprint: {plot_outline}",
            config=types.GenerateContentConfig(system_instruction=runtime_system_instruction, temperature=0.75)
        )
        raw_draft = response.text
        current_prose = raw_draft
        initial_violations = programmatic_violation_check(raw_draft)
        
        max_edits = 3
        for loop_count in range(1, max_edits + 1):
            hard_violations = programmatic_violation_check(current_prose)
            if not hard_violations:
                break
                
            audit_prompt = f"""
            You are an advanced software-driven copyediting compiler. 
            Rewrite the following story text to completely remove these forbidden phrasing violations: {', '.join(hard_violations)}.
            {runtime_system_instruction}
            {current_prose}
            Return ONLY the fully revised, complete story text.
            """
            
            correction_pass = await execute_with_retry_async(
                model=refine_model_target,
                contents=audit_prompt,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            current_prose = correction_pass.text
        
        update_vault_state_from_prose(session_username, current_prose)
        
        stats = telemetry.calculate_prose_telemetry(
            draft_text=raw_draft,
            final_text=current_prose,
            initial_violations=initial_violations,
            checking_function=programmatic_violation_check
        )
        
        stats["tier"] = bundle_config["tier"]
        
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO narrative_logs (username, timestamp, blueprint, manuscript, telemetry_json) 
            VALUES (?, ?, ?, ?, ?)""", 
            (session_username, timestamp_str, plot_outline, current_prose, json.dumps(stats))
        )
        conn.commit()
        conn.close()
        
        upload_history_to_hub()
        return current_prose, stats
        
    except Exception as e:
        error_stats = {"tier": "Error State", "suppression_efficiency_pct": 0, "dialogue_diversity_pct": 0, "lexical_echo_phrases": 0, "pacing_dynamic_range": 0}
        if "503" in str(e):
            return "⏳ Server bottlenecked. Safeguards held. Please wait 10 seconds and compile again!", error_stats
        return f"❌ System Error: {str(e)}", error_stats

def fetch_user_history_choices(username):
    if not username or username == "anonymous":
        return gr.update(choices=[])
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, blueprint FROM narrative_logs WHERE username = ? ORDER BY id DESC", (username,))
    rows = c.fetchall()
    conn.close()
    
    choices = [(f"📅 {row[1]} | Blueprint: {row[2][:35]}...", str(row[0])) for row in rows]
    if not choices:
        return gr.update(choices=[("No history records found for your account", "")], value="")
    return gr.update(choices=choices)

def restore_archived_session(log_id):
    if not log_id:
        return gr.update(), gr.update(), "", {}
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT blueprint, manuscript, telemetry_json FROM narrative_logs WHERE id = ?", (log_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        blueprint, manuscript, telemetry_raw = row[0], row[1], row[2]
        stats = json.loads(telemetry_raw) if telemetry_raw else {}
        
        stats_summary = (
            f"📈 Suppression Efficiency: {stats.get('suppression_efficiency_pct', 100)}%\n"
            f"🎭 Dialogue Diversity Score: {stats.get('dialogue_diversity_pct', 100)}%\n"
        )
        return blueprint, manuscript, stats_summary, stats
    return gr.update(), gr.update(), "", {}

def verify_license_key(username, password):
    username_clean = username.lower().strip()
    password_clean = password.strip()
    if "-" not in password_clean:
        return False
    try:
        expiry_str, client_signature = password_clean.split("-", 1)
        expiry_date = datetime.datetime.strptime(expiry_str, "%Y%m%d").date()
        if datetime.date.today() > expiry_date:
            return False 
            
        raw_string = f"{username_clean}{expiry_str}{SECRET_SALT}"
        expected_signature = hashlib.sha256(raw_string.encode()).hexdigest()[:6]
        return client_signature == expected_signature
    except Exception:
        return False
        
