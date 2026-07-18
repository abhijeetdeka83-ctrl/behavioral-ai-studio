# app.py - Main Application Core & Event Routing Matrix
import os
import inspect
import json
import traceback
import gradio as gr
import engine  
import localization  
from urllib.parse import urlparse

from ui_styles import CUSTOM_CSS
from ui_handlers import (
    execute_gate_login, 
    process_secure_upload,
    async_compilation_handler,
    generate_cover_art,
    trigger_vault_refresh,
    load_historical_file_to_studio
)

from graph_ui_handlers import (
    load_initial_graph,
    generate_visjs_graph,
    get_entity_choices,
    inspect_entity_profile,
    run_ai_timeline_compression,
    populate_continuum_checkboxes,
    run_manual_timeline_compression,
    bootstrap_legacy_story
)

import studio_tab
import graphify_tab
import vault_tab
import sandbox_tab
import archival_tab

engine.init_db()

# ==========================================
# 🔐 SUPABASE CLOUD AUTHENTICATION CONFIG
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError("Missing cloud database cluster credentials (SUPABASE_URL / SUPABASE_ANON_KEY)")
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ==========================================
# 📱 MOBILE RESPONSIVE CSS
# ==========================================
MOBILE_RESPONSIVE_CSS = """
@media (max-width: 768px) {
    .gradio-container { max-width: 100% !important; padding: 8px !important; }
    .workspace-card.landing-container { padding: 16px !important; margin: 5px !important; width: 100% !important; }
    .mobile-input { width: 100% !important; }
    .dynamic-btn { width: 100% !important; font-size: 13px !important; padding: 12px !important; }
    .tabs-navigation > div:first-child, .tabs-navigation .tab-nav { flex-direction: column !important; }
    .tabs-navigation button, .tab-nav button { width: 100% !important; text-align: left !important; padding: 12px 16px !important; }
}
"""

FINAL_CSS_MANIFEST = CUSTOM_CSS + "\n" + MOBILE_RESPONSIVE_CSS

def wrap_html_in_iframe(html_content):
    if not html_content: return ""
    escaped_html = html_content.replace('"', '&quot;')
    return f'<iframe srcdoc="{escaped_html}" width="100%" height="650px" style="border: none; border-radius: 8px; background: transparent;"></iframe>'

# ==========================================
# 🔄 AGGRESSIVE DIAGNOSTIC OAUTH INTERCEPTOR
# ==========================================
OAUTH_JS_INTERCEPTOR = """
function(current_val) {
    try {
        let hash = window.location.hash;
        if (!hash) {
            try { hash = window.parent.location.hash; } catch(e) {}
        }
        
        if (hash && hash.includes("access_token")) {
            let urlParams = new URLSearchParams(hash.substring(1));
            let access = urlParams.get("access_token");
            let refresh = urlParams.get("refresh_token");
            
            if (access && refresh) {
                let payload = JSON.stringify({ access_token: access, refresh_token: refresh });
                localStorage.setItem("stratagem_auth_cache", payload);
                window.history.replaceState({}, document.title, window.location.pathname);
                return payload;
            }
        }
        
        let stored = localStorage.getItem("stratagem_auth_cache");
        return stored ? stored : "";
    } catch (e) {
        return "JS_ERROR: " + e.message;
    }
}
"""

def handle_automated_page_load(session_json):
    """Intercepts, decodes, and brutally logs every failure point during load."""
    if not session_json or not isinstance(session_json, str) or session_json.strip() == "":
        return gr.update(visible=True), gr.update(visible=False), "anonymous", "", gr.update(), gr.update(value="")
        
    if session_json.startswith("JS_ERROR:"):
        return gr.update(visible=True), gr.update(visible=False), "anonymous", "", gr.update(), f"<div style='padding:12px; background:#ffebee; color:#c62828; border-radius:6px; border:1px solid #ffcdd2;'><b>⚠️ Browser Security Block:</b><br>{session_json}</div>"
        
    try:
        # STEP 1: Payload Decoding
        try:
            token_data = json.loads(session_json)
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
        except Exception as e:
            return gr.update(visible=True), gr.update(visible=False), "anonymous", "", gr.update(), f"<div style='padding:12px; background:#ffebee; color:#c62828; border-radius:6px; border:1px solid #ffcdd2;'><b>⚠️ JSON Parsing Failed:</b><br>{str(e)}</div>"

        if not access_token or not refresh_token:
            return gr.update(visible=True), gr.update(visible=False), "anonymous", "", gr.update(), "<div style='padding:12px; background:#ffebee; color:#c62828; border-radius:6px; border:1px solid #ffcdd2;'><b>⚠️ Token Incomplete:</b> Storage cache contains broken token data.</div>"

        # STEP 2: Supabase Authorization Test
        try:
            supabase = get_supabase_client()
            supabase.auth.set_session(access_token=access_token, refresh_token=refresh_token)
            user_response = supabase.auth.get_user()
        except Exception as e:
            return gr.update(visible=True), gr.update(visible=False), "anonymous", "", gr.update(), f"<div style='padding:12px; background:#ffebee; color:#c62828; border-radius:6px; border:1px solid #ffcdd2;'><b>⚠️ Supabase Rejected Session:</b><br>{str(e)}<br><small>Your login may have expired, or your Supabase URL/Anon Key is misconfigured.</small></div>"

        if not user_response or not hasattr(user_response, 'user') or not user_response.user:
            return gr.update(visible=True), gr.update(visible=False), "anonymous", "", gr.update(), "<div style='padding:12px; background:#ffebee; color:#c62828; border-radius:6px; border:1px solid #ffcdd2;'><b>⚠️ User Not Found:</b> Identity verified, but no user data returned.</div>"

        verified_user_identity = user_response.user.email

        # STEP 3: Graph Generation (Isolating the Silent Crasher)
        try:
            html, dropdown_choices = load_initial_graph(verified_user_identity)
            iframe_html = wrap_html_in_iframe(html)
        except Exception as e:
            print(f"Graph rendering crash: {e}")
            # If the graph breaks, we login anyway and show the error!
            iframe_html = f"<div style='padding:20px; background:#fff3e0; color:#e65100; border-radius:8px;'>⚠️ <b>Workspace Graph Failed to Load:</b><br>{str(e)}<br><br><small><i>Your login was successful, but the graph database encountered an error.</i></small></div>"
            dropdown_choices = []

        # STEP 4: Successful Workspace Boot
        return (
            gr.update(visible=False), 
            gr.update(visible=True), 
            verified_user_identity, 
            iframe_html, 
            gr.update(choices=dropdown_choices),
            gr.update(value="")
        )

    except Exception as critical_error:
        error_trace = traceback.format_exc()
        print(f"Critical System Failure: {error_trace}")
        return gr.update(visible=True), gr.update(visible=False), "anonymous", "", gr.update(), f"<div style='padding:12px; background:#ffebee; color:#c62828; border-radius:6px; border:1px solid #ffcdd2;'><b>⚠️ System Failure:</b><br>{str(critical_error)}</div>"

# ==========================================
# 🧱 APP INTERFACE CONSTRUCTOR
# ==========================================
with gr.Blocks() as demo:
    session_user = gr.State("anonymous")
    oauth_token_bridge = gr.Textbox(visible=False)
    
    with gr.Column(visible=True, elem_classes="workspace-card landing-container") as landing_gate:
        gr.Markdown("## 🤖 STRATAGEM WORKSPACE BETA")
        gr.Markdown(
            """
            ### 🎁 EARLY-BIRD FOUNDER STATUS (BETA)
            Thank you for helping us test the workspace! By using this app during our official **Beta Phase**, you are automatically locked in as a founding user. 
            
            **Your Benefit:** You will receive **1 Year of Premium Subscription completely FREE** on the day of our official public launch.
            """
        )
        
        status_notification = gr.HTML("")
        
        with gr.Group():
            github_auth_trigger = gr.Button("Sign in with GitHub", variant="secondary", elem_classes="action-btn dynamic-btn")
            github_link_display = gr.HTML(visible=False)
            
        gr.Markdown("<p style='text-align: center; color: #777; margin: 15px 0;'>— OR USE YOUR EMAIL —</p>")
        email_field = gr.Textbox(label="Email Address", placeholder="name@example.com", lines=1, elem_classes="mobile-input")
        password_field = gr.Textbox(label="Password", placeholder="••••••••", type="password", lines=1, elem_classes="mobile-input")
        submit_gate_btn = gr.Button("Sign In", variant="primary", elem_classes="action-btn dynamic-btn")

    with gr.Column(visible=False) as main_workspace:
        with gr.Group(elem_classes="header-container"):
            gr.Markdown("# 🤖 CORE STRATAGEM WORKSPACE", elem_classes="brand-title")
            user_counter_display = gr.Markdown("📊 Counting active nodes...")
        
        with gr.Tabs(elem_classes="tabs-navigation"):
            with gr.Tab("🚀 Interactive AI Studio"):
                st = studio_tab.render_studio_tab()
            with gr.Tab("🛰️ Graphify Interactive Map"):
                gt = graphify_tab.render_graphify_tab()
            with gr.Tab("📁 Vault File Explorer"):
                vt = vault_tab.render_vault_tab()
            with gr.Tab("🎨 Illustration Sandbox"):
                sb = sandbox_tab.render_sandbox_tab()
            with gr.Tab("🛰️ Graphify Memory Archival"):
                at = archival_tab.render_archival_tab()

    # 🛡️ SAFE INTERCEPT WRAPPERS
    def safe_identify_key_handler(api_key):
        try: return engine.identify_key_and_filter_bundles(api_key)
        except Exception as e: return gr.update(choices=["Error validating bundle setup"], value="Error validating bundle setup"), f"❌ **Key Token Error:** {str(e)}"

    async def safe_async_compilation_handler(*args):
        try:
            if inspect.iscoroutinefunction(async_compilation_handler): return await async_compilation_handler(*args)
            return async_compilation_handler(*args)
        except Exception as e: return f"❌ COMPILATION CRASH: {str(e)}", "OFFLINE_TIER", 0, 0, 0, 0, f"Diagnostic Logs:\n{str(e)}"

    async def safe_bootstrap_legacy_handler(*args):
        try:
            if inspect.iscoroutinefunction(bootstrap_legacy_story): return await bootstrap_legacy_story(*args)
            return bootstrap_legacy_story(*args)
        except Exception as e: return f"❌ Legacy Extraction Agent Failure: {str(e)}"

    def safe_translate_manuscript_handler(text, lang, key):
        try: return localization.translate_manuscript(text, lang, key)
        except Exception as e: return f"❌ Translation Engine Blocked: {str(e)}\n\n[Original Source Text]:\n{text}"
        
    def safe_load_initial_graph_wrapper(user):
        try:
            html, choices = load_initial_graph(user)
            return wrap_html_in_iframe(html), choices
        except Exception as e:
            return f"<p style='color:red'>Graph Gen Error: {e}</p>", []

    def safe_refresh_visualization_wrapper(user, search, f_type):
        try:
            html = generate_visjs_graph(user, search, f_type)
            choices = get_entity_choices(user)
            return wrap_html_in_iframe(html), choices
        except Exception as e:
            return f"<p style='color:red'>Refresh Error: {e}</p>", []

    # 🎛️ EVENT HANDLERS & WIRE ROUTING
    def generate_github_oauth_handshake(request: gr.Request):
        try:
            supabase = get_supabase_client()
            res = supabase.auth.sign_in_with_oauth({"provider": "github"})
            authentic_button_html = f"""
            <div style="display: flex; justify-content: center; width: 100%; margin: 12px 0;">
                <a href="{res.url}" target="_top" style="display: inline-flex; align-items: center; justify-content: center; background-color: #24292e; color: #ffffff; text-decoration: none; font-family: sans-serif; font-size: 15px; font-weight: 600; padding: 12px 24px; border-radius: 6px; width: 100%; max-width: 340px; text-align: center;">
                    Sign in with GitHub Redirect
                </a>
            </div>
            """
            return gr.update(value=authentic_button_html, visible=True)
        except Exception as e: return gr.update(value=f"<p style='color: red;'>❌ OAuth Failure: {str(e)}</p>", visible=True)

    github_auth_trigger.click(fn=generate_github_oauth_handshake, inputs=None, outputs=[github_link_display])
    
    submit_gate_btn.click(
        fn=execute_gate_login, inputs=[email_field, password_field], outputs=[landing_gate, main_workspace, st["key_status_box"], user_counter_display, session_user]
    ).then(fn=safe_load_initial_graph_wrapper, inputs=[session_user], outputs=[gt["graph_html_output"], gt["inspect_dropdown"]])
    
    st["api_input"].change(fn=safe_identify_key_handler, inputs=[st["api_input"]], outputs=[st["bundle_dropdown"], st["key_status_box"]])
    st["api_input"].blur(fn=safe_identify_key_handler, inputs=[st["api_input"]], outputs=[st["bundle_dropdown"], st["key_status_box"]])
    
    st["submit_btn"].click(
        fn=safe_async_compilation_handler, 
        inputs=[st["api_input"], st["outline_input"], st["bundle_dropdown"], st["pinned_entities"], st["genre_input"], st["ui_pacing_mode"], st["ui_prose_density"], st["ui_dialogue_intensity"], st["ui_description_level"], st["ui_world_visibility"], st["ui_emotional_opacity"], session_user], 
        outputs=[st["output_text"], st["ui_tier_badge"], st["ui_efficiency_slider"], st["ui_diversity_slider"], st["ui_echo_badge"], st["ui_pacing_badge"], st["ui_rag_telemetry"]],  
        show_progress="full"
    ).then(fn=safe_load_initial_graph_wrapper, inputs=[session_user], outputs=[gt["graph_html_output"], gt["inspect_dropdown"]])
    
    st["bootstrap_btn"].click(fn=safe_bootstrap_legacy_handler, inputs=[session_user, st["api_input"], st["bundle_dropdown"], st["legacy_draft_box"]], outputs=[st["bootstrap_status"]]).then(fn=safe_load_initial_graph_wrapper, inputs=[session_user], outputs=[gt["graph_html_output"], gt["inspect_dropdown"]])
    
    gt["refresh_graph_btn"].click(fn=safe_refresh_visualization_wrapper, inputs=[session_user, gt["search_box"], gt["type_filter"]], outputs=[gt["graph_html_output"], gt["inspect_dropdown"]])
    gt["search_box"].change(fn=safe_refresh_visualization_wrapper, inputs=[session_user, gt["search_box"], gt["type_filter"]], outputs=[gt["graph_html_output"], gt["inspect_dropdown"]])
    gt["type_filter"].change(fn=safe_refresh_visualization_wrapper, inputs=[session_user, gt["search_box"], gt["type_filter"]], outputs=[gt["graph_html_output"], gt["inspect_dropdown"]])
    gt["inspect_dropdown"].change(fn=inspect_entity_profile, inputs=[session_user, gt["inspect_dropdown"]], outputs=[gt["inspector_panel_md"]])
    
    at["ai_compress_btn"].click(fn=run_ai_timeline_compression, inputs=[session_user, st["api_input"], st["bundle_dropdown"]], outputs=[at["operation_log_output"]]).then(fn=safe_load_initial_graph_wrapper, inputs=[session_user], outputs=[gt["graph_html_output"], gt["inspect_dropdown"]])
    at["scan_timeline_btn"].click(fn=populate_continuum_checkboxes, inputs=[session_user], outputs=[at["preservation_checkboxes"]])
    at["manual_compress_btn"].click(fn=run_manual_timeline_compression, inputs=[session_user, at["preservation_checkboxes"]], outputs=[at["operation_log_output"]]).then(fn=safe_load_initial_graph_wrapper, inputs=[session_user], outputs=[gt["graph_html_output"], gt["inspect_dropdown"]])
    
    st["translate_btn"].click(fn=safe_translate_manuscript_handler, inputs=[st["output_text"], st["language_dropdown"], st["api_input"]], outputs=[st["output_text"]])
    st["file_uploader"].upload(fn=process_secure_upload, inputs=[st["file_uploader"], session_user], outputs=st["upload_status"])
    sb["generate_art_btn"].click(fn=generate_cover_art, inputs=[sb["art_prompt"], sb["style_dropdown"]], outputs=[sb["gallery_output"]])
    vt["refresh_vault_btn"].click(fn=trigger_vault_refresh, inputs=[session_user], outputs=[vt["history_dropdown"], vt["vault_grid"]])
    
    vt["history_dropdown"].change(fn=load_historical_file_to_studio, inputs=[vt["history_dropdown"]], outputs=[st["outline_input"], st["output_text"], st["ui_tier_badge"], st["ui_efficiency_slider"], st["ui_diversity_slider"], st["ui_echo_badge"], st["ui_pacing_badge"], st["ui_rag_telemetry"]])

    # 🔗 THE ALARM SYSTEM
    demo.load(
        fn=handle_automated_page_load,
        inputs=[oauth_token_bridge],
        outputs=[landing_gate, main_workspace, session_user, gt["graph_html_output"], gt["inspect_dropdown"], status_notification],
        js=OAUTH_JS_INTERCEPTOR
    )

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=10)
    demo.launch(server_name="0.0.0.0", server_port=7860, css=FINAL_CSS_MANIFEST)
