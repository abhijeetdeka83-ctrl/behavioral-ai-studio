import gradio as gr

def render_graphify_tab():
    components = {}
    with gr.Row():
        components["search_box"] = gr.Textbox(label="🔍 Filter Nodes / Search Entities", placeholder="Enter Character name...", scale=4)
        components["type_filter"] = gr.Dropdown(choices=["All", "Character", "Location", "Artifact"], value="All", label="Filter Entity Classification Type", scale=4)
        components["refresh_graph_btn"] = gr.Button("🔄 REBUILD INTERACTIVE MAP", elem_classes="action-btn secondary-btn", scale=2)
        
    with gr.Row():
        with gr.Column(scale=7, elem_classes="workspace-card"):
            components["graph_html_output"] = gr.HTML(label="Active Topological Network View")
            
        with gr.Column(scale=3, elem_classes="workspace-card"):
            gr.Markdown("### 🔍 Continuum Profile Inspector")
            components["inspect_dropdown"] = gr.Dropdown(label="Select Discovered Node Profile to Inspect", choices=[], interactive=True)
            components["inspector_panel_md"] = gr.Markdown("### Profile Preview Staging Window\nSelect a node above to view attributes.")

    return components
    
