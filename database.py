import os
import json
import datetime
import re
import concurrent.futures  # High-performance asynchronous timeout worker engine
import gradio as gr
from supabase import create_client, Client

# Automatically inherit your secure space connection credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"❌ [Supabase Client Failure]: {e}")

def init_db():
    """Schemas are managed via Supabase Dashboard now. Purely operational check."""
    if supabase:
        print("⚡ [Database Core] Connected instantly to live cloud clusters.")
    else:
        print("⚠️ [Database Core] Offline. Missing environmental credentials.")

def register_beta_user(email):
    if not supabase: 
        print("⚠️ [Database Core] Supabase client offline baseline default triggered.")
        return 0
        
    clean_email = email.strip().lower()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Isolated execution unit to balance cloud synchronization latency
    def run_cloud_sync():
        # --- Dual-Column Fallback Matrix ---
        try:
            # Route 1: Attempt write to custom schema layout
            supabase.table("beta_users").insert({"email": clean_email, "signup_date": current_time}).execute()
        except Exception as e1:
            print(f"ℹ️ [Database Notice] Primary layout key 'signup_date' rejected: {e1}")
            try:
                # Route 2: Fallback automatically to standard default Supabase timestamp naming
                supabase.table("beta_users").insert({"email": clean_email, "created_at": current_time}).execute()
                print("✅ [Database Recovery] Fallback registration route successfully committed.")
            except Exception as e2:
                print(f"❌ [Database Failure] Fallback write matrix rejected: {e2}")
            
        # Get live dynamic count of registered founding users
        try:
            count_res = supabase.table("beta_users").select("id", count="exact").execute()
            return count_res.count if count_res.count is not None else 0
        except Exception as e:
            print(f"❌ [Database Core Error] Failed to fetch dynamic network scale: {e}")
            return 0

    # Execute inside a thread with a strict 5.0 second maximum network cutoff threshold
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_cloud_sync)
        try:
            return future.result(timeout=5.0)
        except concurrent.futures.TimeoutError:
            print("⚠️ [Database Timeout] Cloud transaction dropped safely to protect dashboard lifecycle.")
            return 0
        except Exception as e:
            print(f"❌ [Database Core Crash] Thread validation failed: {e}")
            return 0

def compile_active_state_manifest(username: str) -> str:
    if not supabase: return "🏆 Cloud link down."
    
    try:
        res = supabase.table("vault_state_registry").select("state_json").eq("username", username).execute()
        state = res.data[0]["state_json"] if res.data else {"environment_degradation": ["No severe structural anomalies logged"], "character_knowledge_flags": {}}
    except Exception:
        state = {"environment_degradation": ["No severe structural anomalies logged"], "character_knowledge_flags": {}}
        
    char_flags = state.get('character_knowledge_flags', {})
    char_lines = [f"{char_name} Knowledge Base: {', '.join(flags)}" for char_name, flags in char_flags.items()]
    if not char_lines:
        char_lines.append("No explicit character knowledge baselines tracked yet.")
        
    return f"""
    <LAYER_2_ACTIVE_STATE>
    Environmental Degradation Tracking: {', '.join(state.get('environment_degradation', ['No anomalies logged']))}
    {"\n    ".join(char_lines)}
    </LAYER_2_ACTIVE_STATE>
    """

def update_vault_state_from_prose(username: str, script_text: str):
    if not supabase: return
    
    try:
        res = supabase.table("vault_state_registry").select("state_json").eq("username", username).execute()
        state = res.data[0]["state_json"] if res.data else {"environment_degradation": [], "character_knowledge_flags": {}}
    except Exception:
        state = {"environment_degradation": [], "character_knowledge_flags": {}}
    
    if re.search(r"\b(broke|shattered|tore|spilled|leaked|sheared|failed|cracked|ruined|smashed)\b", script_text, re.IGNORECASE):
        timestamp_now = datetime.datetime.now().strftime("%H:%M")
        state["environment_degradation"].append(f"Material structural decay trace verified at {timestamp_now}")
        
    state["environment_degradation"] = list(set(state["environment_degradation"]))[-4:]
    
    # Save directly back up via UPSERT (Insert new row or override existing key records instantly)
    try:
        supabase.table("vault_state_registry").upsert({"username": username, "state_json": state}).execute()
    except Exception as e:
        print(f"❌ Failed to push structural context updates: {e}")

def fetch_user_history_choices(username):
    if not username or username == "anonymous" or not supabase:
        return gr.update(choices=[])
        
    try:
        res = supabase.table("narrative_logs")\
            .select("id", "timestamp", "blueprint")\
            .eq("username", username)\
            .order("id", desc=True)\
            .execute()
        rows = res.data
    except Exception:
        rows = []
        
    choices = [(f"📅 {row['timestamp']} | Blueprint: {row['blueprint'][:35]}...", str(row['id'])) for row in rows]
    return gr.update(choices=choices) if choices else gr.update(choices=[("No history records found for your account", "")], value="")

def restore_archived_session(log_id):
    if not log_id or not supabase:
        return gr.update(), gr.update(), "", {}
        
    try:
        res = supabase.table("narrative_logs").select("blueprint", "manuscript", "telemetry_json").eq("id", log_id).execute()
        if res.data:
            row = res.data[0]
            blueprint, manuscript = row["blueprint"], row["manuscript"]
            stats = row["telemetry_json"] if isinstance(row["telemetry_json"], dict) else json.loads(row["telemetry_json"] or "{}")
            stats_summary = f"📈 Suppression Efficiency: {stats.get('suppression_efficiency_pct', 100)}%\n🎭 Dialogue Diversity Score: {stats.get('dialogue_diversity_pct', 100)}%\n"
            return blueprint, manuscript, stats_summary, stats
    except Exception as e:
        print(f"❌ Session recovery crashed: {e}")
        
    return gr.update(), gr.update(), "", {}
    
