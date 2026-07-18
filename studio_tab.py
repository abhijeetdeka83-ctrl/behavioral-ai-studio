import gradio as gr
import localization

def render_studio_tab():
    components = {}
    with gr.Row():
        with gr.Column(scale=4, elem_classes="workspace-card"):
            gr.Markdown("### 🛠️ Operation Inputs")
            components["api_input"] = gr.Textbox(
                label="🔑 Active Workspace API Token / Core License Key", 
                placeholder="Paste your Gemini, OpenAI, Anthropic, or Open-Source token...",
                type="password"
            )
            components["key_status_box"] = gr.Markdown("⚪ **Status:** Staging window is currently idle.", elem_classes="status-badge")
            
            components["bundle_dropdown"] = gr.Dropdown(
                choices=["Please input an API key to unlock bundles"], 
                value="Please input an API key to unlock bundles", 
                label="📦 Select AI Engine Structure",
                interactive=True
            )
            
            with gr.Accordion("🎭 Advanced V5 Narrative & Pacing Profiles", open=True):
                components["genre_input"] = gr.Dropdown(choices=["Fantasy", "Sci-Fi", "Grimdark Epic", "Slice of Life"], value="Fantasy", label="Target Genre", allow_custom_value=True)
                components["ui_pacing_mode"] = gr.Dropdown(choices=["Slow_Burn", "Balanced", "High_Momentum"], value="Slow_Burn", label="Pacing Execution Strategy")
                with gr.Row():
                    components["ui_prose_density"] = gr.Dropdown(choices=["Dense", "Standard", "Lean"], value="Dense", label="Prose Density")
                    components["ui_dialogue_intensity"] = gr.Dropdown(choices=["Minimal", "Natural", "Conversation_Heavy"], value="Natural", label="Dialogue Intensity")
                with gr.Row():
                    components["ui_description_level"] = gr.Dropdown(choices=["Low", "Medium", "High"], value="High", label="Description Level")
                    components["ui_world_visibility"] = gr.Dropdown(
                        choices=["Character", "Environmental", "Balanced"], 
                        value="Balanced", 
                        label="World Visibility View"
                    )
                components["ui_emotional_opacity"] = gr.Dropdown(choices=["Explicit", "Balanced", "Behavioral"], value="Behavioral", label="Emotional Opacity")
            
            components["pinned_entities"] = gr.Textbox(label="📌 Pinned Entity Profiles (Manual Override)", lines=4)
            components["outline_input"] = gr.Textbox(label="📝 Structure Blueprint / Prompts", lines=10)
            components["file_uploader"] = gr.File(label="📎 Attach Lore Map (Max 5MB)")
            components["upload_status"] = gr.Textbox(label="Asset Verification Status", interactive=False)
            
            with gr.Accordion("📚 Import Legacy Chapters", open=False):
                components["legacy_draft_box"] = gr.Textbox(label="Paste Your Existing Chapters / Story Text", lines=10)
                components["bootstrap_btn"] = gr.Button("⚡ ANALYZE & BOOTSTRAP LEGACY LORE", elem_classes="action-btn secondary-btn")
                components["bootstrap_status"] = gr.Textbox(label="Extraction Agent Status Logs", interactive=False)
            
            components["language_dropdown"] = gr.Dropdown(choices=list(localization.TARGET_LANGUAGES.keys()), value="Japanese (日本語)", label="Global Translation")
            components["translate_btn"] = gr.Button("🌐 EXECUTE REGIONAL TRANSLATION", elem_classes="action-btn secondary-btn")
            components["submit_btn"] = gr.Button("⚡ RUN COMPILATION QUEUE", variant="primary", elem_classes="action-btn")
            
        with gr.Column(scale=6, elem_classes="workspace-card"):
            gr.Markdown("### 📜 Output Console")
            components["output_text"] = gr.Textbox(label="Latest Compiled Manuscript", lines=14, elem_classes="manuscript-canvas")
            
            gr.Markdown("### 🛰️ Layer 4 Narrative Telemetry Analytics Dashboard")
            with gr.Group(elem_classes="kpi-container"):
                with gr.Row():
                    components["ui_tier_badge"] = gr.Textbox(label="🏷️ Active Quota Footprint Tier", interactive=False)
                    components["ui_echo_badge"] = gr.Number(label="🔄 Lexical Echo Phrases Caught", interactive=False)
                with gr.Row():
                    components["ui_efficiency_slider"] = gr.Slider(label="📈 Forbidden Phrase Suppression Efficiency", interactive=False)
                    components["ui_diversity_slider"] = gr.Slider(label="🎭 Dialogue Diversity Score", interactive=False)
                with gr.Row():
                    components["ui_pacing_badge"] = gr.Number(label="⏳ Pacing Dynamic Range", interactive=False)
                components["ui_rag_telemetry"] = gr.Textbox(label="🛰️ Layer 4 Deep Runtime Matrix & Token Logs", lines=6, interactive=False)

    return components
    
