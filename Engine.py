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
import telemetry  # 🌟 Layer 4 Integration

DB_FILE = "narrative_history.db"
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_DATASET_ID = os.environ.get("HF_DATASET_ID")
SECRET_SALT = os.environ.get("SECRET_BOUNDARIES_SALT", "super_secret_fallback_phrase_99")
SECRET_BOUNDARIES = os.environ.get("STRUCTURAL_BOUNDARIES", "Error: Prompt constraints missing.")

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
    # Historic repository archive logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS narrative_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            blueprint TEXT,
            manuscript TEXT
        )
    ''')
    # Safe migration: Ensure older database instances get the telemetry column automatically
    try:
        c.execute("ALTER TABLE narrative_logs ADD COLUMN telemetry_json TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # LAYER 2 STATE MATRIX: Tracks continuous environmental memory per workspace user
    c.execute('''
        CREATE TABLE IF NOT EXISTS vault_state_registry (
            username TEXT PRIMARY KEY,
            state_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def compile_active_state_manifest(username: str) -> str:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT state_json FROM vault_state_registry WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        default_state = {
            "environment_degradation": ["No severe structural anomalies logged"],
            "character_knowledge_flags": {
                "Garrick": ["Aware of baseline mechanical operational limits"],
                "Toby": ["Aware of immediate surface-level neighborhood occurrences"]
            }
        }
        return f"""
        <LAYER_2_ACTIVE_STATE>
        Environmental Degradation Tracking: {', '.join(default_state['environment_degradation'])}
        Garrick Knowledge Base: {', '.join(default_state['character_knowledge_flags']['Garrick'])}
        Toby Knowledge Base: {', '.join(default_state['character_knowledge_flags']['Toby'])}
        </LAYER_2_ACTIVE_STATE>
        """
        
    state = json.loads(row[0])
    return f"""
    <LAYER_2_ACTIVE_STATE>
    Environmental Degradation Tracking: {', '.join(state.get('environment_degradation', ['No anomalies logged']))}
    Garrick Knowledge Base: {', '.join(state.get('character_knowledge_flags', {}).get('Garrick', ['Baseline logic']))}
    Toby Knowledge Base: {', '.join(state.get('character_knowledge_flags', {}).get('Toby', ['Baseline logic']))}
    </LAYER_2_ACTIVE_STATE>
    """

def update_vault_state_from_prose(username: str, script_text: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT state_json FROM vault_state_registry WHERE username = ?", (username,))
    row = c.fetchone()
    
    state = json.loads(row[0]) if row else {
        "environment_degradation": [],
        "character_knowledge_flags": {"Garrick": [], "Toby": []}
    }
    
    if re.search(r"\b(broke|shattered|tore|spilled|leaked|sheared|failed|cracked|ruined|smashed)\b", script_text, re.IGNORECASE):
        timestamp_now = datetime.datetime.now().strftime("%H:%M")
        state["environment_degradation"].append(f"Material structural decay trace verified at {timestamp_now}")
        
    state["environment_degradation"] = list(set(state["environment_degradation"]))[-4:]
    
    c.execute("INSERT OR REPLACE INTO vault_state_registry (username, state_json) VALUES (?, ?)", (username, json.dumps(state)))
    conn.commit()
    conn.close()

def programmatic_violation_check(text):
    forbidden_patterns = [
        r"\brealized\b", r"\bunderstood\b", r"\bfelt\b", 
        r"\bcouldn't help but feel\b", r"\bfor the first time\b", 
        r"\bthe moment stayed\b", r"\bit bothered\b", r"\bshe knew\b", r"\bhe knew\b",
        r",\s*(Garrick|Toby)[\.!]",
        r"\bwith the weight of\b", r"\bas if to say\b", r"\bseemed to symbolize\b"
    ]
    violations = []
    for pattern in forbidden_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            violations.append(f"'{matches[0]}'")
    return violations

async def generate_story(buyer_api_key, plot_outline, request: gr.Request):
    if not buyer_api_key.strip() or not plot_outline.strip():
        return "🚨 System Status: Execution halted. Required fields are empty.", "No telemetry logged."
    
    username = request.username if request else "anonymous"
        
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

        live_state_manifest = compile_active_state_manifest(username)
        runtime_system_instruction = f"{SECRET_BOUNDARIES}\n\n{live_state_manifest}"

        # --- PASS 1: THE INITIAL DRAFT ---
        response = await execute_with_retry_async(
            model="gemini-3.5-flash",
            contents=f"Execute the next structural scene based on this user blueprint: {plot_outline}",
            config=types.GenerateContentConfig(system_instruction=runtime_system_instruction, temperature=0.75)
        )
        raw_draft = response.text
        current_prose = raw_draft
        
        # 🌟 Capture initial baseline violations before editing wipes them clean
        initial_violations = programmatic_violation_check(raw_draft)
        
        # --- PASS 2+: CRITIQUE REFINEMENT PIPELINE ---
        max_edits = 3
        for loop_count in range(1, max_edits + 1):
            hard_violations = programmatic_violation_check(current_prose)
            if not hard_violations:
                break
                
            audit_prompt = f"""
            You are an advanced software-driven copyediting compiler. 
            Rewrite the following story text to completely remove these forbidden phrasing violations: {', '.join(hard_violations)}.
            
            [IMMUTABLE CRITERIA HIERARCHY & DYNAMIC WORLD STATES]
            {runtime_system_instruction}
            
            [TARGET MANUSCRIPT TEXT TO DE-AI]
            {current_prose}
            
            Return ONLY the fully revised, complete story text. Do not include notes or commentary.
            """
            
            correction_pass = await execute_with_retry_async(
                model="gemini-2.5-flash",
                contents=audit_prompt,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            current_prose = correction_pass.text
        
        update_vault_state_from_prose(username, current_prose)
        
        # 🌟 LAYER 4 PROCESSING: Compile comparative performance metrics
        stats = telemetry.calculate_prose_telemetry(
            draft_text=raw_draft,
            final_text=current_prose,
            initial_violations=initial_violations,
            checking_function=programmatic_violation_check
        )
        
        # --- COMMIT LOG INTO USER TIMELINE ---
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO narrative_logs (username, timestamp, blueprint, manuscript, telemetry_json) 
            VALUES (?, ?, ?, ?, ?)""", 
            (username, timestamp_str, plot_outline, current_prose, json.dumps(stats))
        )
        conn.commit()
        conn.close()
        
        upload_history_to_hub()
        
        # Build scannable telemetry text block output for the UI panel
        stats_summary = (
            f"📈 Suppression Efficiency: {stats['suppression_efficiency_pct']}%\n"
            f"🎭 Dialogue Diversity Score: {stats['dialogue_diversity_pct']}%\n"
            f"🔄 Lexical Echo Phrases Caught: {stats['lexical_echo_phrases']}\n"
            f"⏳ Pacing Dynamic Range (Sentence StdDev): {stats['pacing_dynamic_range']} words\n"
            f"🔀 Word Count Delta: {stats['word_count_delta']} words"
        )
        return current_prose, stats_summary
        
    except Exception as e:
        if "503" in str(e):
            return "⏳ Server bottlenecked. Safeguards held. Please wait 10 seconds and compile again!", "N/A"
        return f"❌ System Error: {str(e)}", "Error compiling telemetry."

def fetch_user_history_choices(request: gr.Request):
    if not request or not request.username:
        return gr.update(choices=[])
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, blueprint FROM narrative_logs WHERE username = ? ORDER BY id DESC", (request.username,))
    rows = c.fetchall()
    conn.close()
    
    choices = [(f"📅 {row[1]} | Blueprint: {row[2][:35]}...", str(row[0])) for row in rows]
    if not choices:
        return gr.update(choices=[("No history records found for your account", "")], value="")
    return gr.update(choices=choices)

def restore_archived_session(log_id):
    if not log_id:
        return gr.update(), gr.update(), gr.update()
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT blueprint, manuscript, telemetry_json FROM narrative_logs WHERE id = ?", (log_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        blueprint, manuscript, telemetry_raw = row[0], row[1], row[2]
        if telemetry_raw:
            stats = json.loads(telemetry_raw)
            stats_summary = (
                f"📈 Suppression Efficiency: {stats.get('suppression_efficiency_pct', 100)}%\n"
                f"🎭 Dialogue Diversity Score: {stats.get('dialogue_diversity_pct', 100)}%\n"
                f"🔄 Lexical Echo Phrases Caught: {stats.get('lexical_echo_phrases', 0)}\n"
                f"⏳ Pacing Dynamic Range (Sentence StdDev): {stats.get('pacing_dynamic_range', 0)} words\n"
                f"🔀 Word Count Delta: {stats.get('word_count_delta', 0)} words"
            )
        else:
            stats_summary = "Historical entry: Telemetry registry log not present for this entry."
            
        return blueprint, manuscript, stats_summary
    return gr.update(), gr.update(), gr.update()

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
        
