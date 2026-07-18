import gradio as gr

def render_sandbox_tab():
    components = {}
    with gr.Row():
        with gr.Column(scale=4, elem_classes="workspace-card"):
            gr.Markdown("### 📐 Cover & Scenic Concepts")
            components["art_prompt"] = gr.Textbox(label="Visual Scene Description / Prompt", lines=5)
            components["style_dropdown"] = gr.Dropdown(choices=["Fantasy Novel Illustration", "Oil Pastel Canvas", "Dark Obsidian Vector Paint"], value="Fantasy Novel Illustration", label="Artistic Stylization Frame")
            components["generate_art_btn"] = gr.Button("🎨 RENDER COVER ARTWORK", variant="primary", elem_classes="action-btn")
        with gr.Column(scale=6, elem_classes="workspace-card"):
            gr.Markdown("### 🖼️ Conceptual Gallery Window")
            components["gallery_output"] = gr.Image(label="Latest Compiled Staging Asset", interactive=False)
            
    return components
    
