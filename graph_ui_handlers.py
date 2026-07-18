# graph_ui_handlers.py - Isolated UI Helper Logic for Graphify Mapping Tab
import json
import os
import re
import time
import gradio as gr
import engine
from graph_memory import GraphifyStoryMemory
from hf_storage import upload_vault_asset_to_hub

# =========================================================================
# 🛰️ GRAPHIFY INTERACTIVE VISUALIZATION & INSPECTOR LOGIC
# =========================================================================

def load_initial_graph(username):
    """Initializes and pre-loads the dynamic graph network upon logging in."""
    if not username or username == "anonymous":
        return (
            gr.update(value="<p style='color:#64748b;'>Please initialize your session core to unlock mapping streams.</p>"), 
            gr.update(choices=[])
        )
    html_view = generate_visjs_graph(username)
    choices = get_entity_choices(username)
    return html_view, choices

def get_entity_choices(username):
    """Pulls current entities to populate the dropdown inspector select element."""
    memory = GraphifyStoryMemory()
    graph = memory.load_graph(username)
    nodes = list(graph.get("nodes", {}).keys())
    if not nodes:
        return gr.update(choices=[("No entities discovered yet", "")], value="")
    return gr.update(choices=[(n, n) for n in nodes], value=nodes[0] if nodes else "")

def generate_visjs_graph(username, search_query="", type_filter="All"):
    """
    Renders a stunning Vis.js dynamic network visualizer directly inside 
    the Dark Obsidian styled workspace. Fully draggable, physics-enabled, and zoomable.
    """
    memory = GraphifyStoryMemory()
    graph = memory.load_graph(username)
    
    nodes_data = []
    edges_data = []
    
    # Custom Gradient-complementary color palette mapping for Dark Obsidian Style
    color_map = {
        "Character": {"background": "#7c3aed", "border": "#a78bfa", "highlight": "#9333ea"},
        "Location": {"background": "#0d9488", "border": "#2dd4bf", "highlight": "#0f766e"},
        "Artifact": {"background": "#ea580c", "border": "#fb923c", "highlight": "#c2410c"},
        "Concept": {"background": "#4b5563", "border": "#9ca3af", "highlight": "#374151"}
    }
    
    for node_id, info in graph.get("nodes", {}).items():
        node_type = info.get("type", "Concept")
        
        # Apply Live Workspace Filters
        if type_filter != "All" and node_type != type_filter:
            continue
        if search_query and search_query.lower() not in node_id.lower():
            continue
            
        colors = color_map.get(node_type, color_map["Concept"])
        nodes_data.append({
            "id": node_id,
            "label": node_id,
            "title": f"Type: {node_type}<br>Status: {info.get('status', 'N/A')}<br>Discovered Turn: #{info.get('discovered_at_turn', 1)}",
            "color": colors,
            "font": {"color": "#f1f5f9", "size": 14, "bold": True},
            "shape": "dot",
            "size": 25 if node_type == "Character" else 18
        })
        
    filtered_node_ids = {n["id"] for n in nodes_data}
    for edge in graph.get("edges", []):
        if edge["source"] in filtered_node_ids and edge["target"] in filtered_node_ids:
            edges_data.append({
                "from": edge["source"],
                "to": edge["target"],
                "label": edge["relation"],
                "color": {"color": "#475569", "highlight": "#6366f1"},
                "font": {"color": "#cbd5e1", "size": 11, "strokeWidth": 0, "align": "horizontal"},
                "arrows": "to"
            })
            
    nodes_json = json.dumps(nodes_data)
    edges_json = json.dumps(edges_data)
    
    html_code = f"""
    <div style="width: 100%; height: 530px; background-color: #04060a; border: 1px solid #1e293b; border-radius: 12px; overflow: hidden; position: relative;">
        <div id="vis_network" style="width: 100%; height: 100%;"></div>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <script type="text/javascript">
            function initNetwork() {{
                var container = document.getElementById('vis_network');
                if (!container) return;
                
                var data = {{
                    nodes: new vis.DataSet({nodes_json}),
                    edges: new vis.DataSet({edges_json})
                }};
                
                var options = {{
                    nodes: {{
                        borderWidth: 2,
                        shadow: true
                    }},
                    edges: {{
                        width: 2,
                        shadow: true,
                        smooth: {{
                            enabled: true,
                            type: 'dynamic',
                            roundness: 0.5
                        }}
                    }},
                    physics: {{
                        enabled: true,
                        solver: 'forceAtlas2Based',
                        forceAtlas2Based: {{
                            gravitationalConstant: -70,
                            centralGravity: 0.015,
                            springLength: 130,
                            springConstant: 0.08,
                            damping: 0.4
                        }},
                        stabilization: {{
                            enabled: true,
                            iterations: 150,
                            updateInterval: 25
                        }}
                    }},
                    interaction: {{
                        hover: true,
                        navigationButtons: true,
                        keyboard: true
                    }}
                }};
                
                var network = new vis.Network(container, data, options);
            }}
            
            if (typeof vis !== 'undefined') {{
                initNetwork();
            }} else {{
                var interval = setInterval(function() {{
                    if (typeof vis !== 'undefined') {{
                        initNetwork();
                        clearInterval(interval);
                    }}
                }}, 100);
            }}
        </script>
    </div>
    """
    return html_code

def inspect_entity_profile(username, entity_name):
    """Compiles a gorgeous dynamic status dossier markdown sheet for chosen entities."""
    if not username or username == "anonymous" or not entity_name:
        return "### 🔍 Entity Inspector\nSelect an active entity to visualize its status profile and relational connections."
        
    memory = GraphifyStoryMemory()
    graph = memory.load_graph(username)
    
    node_info = graph.get("nodes", {}).get(entity_name)
    if not node_info:
        return f"### ❌ Error\nEntity '**{entity_name}**' could not be mapped inside the current timeline state graph."
        
    report = [
        f"## 🛰️ {entity_name}",
        f"**Classification:** `{node_info.get('type', 'Concept')}`",
        f"**Active Status:** *{node_info.get('status', 'Discovered')}*",
        f"**Discovery Temporal Marker:** `Turn #{node_info.get('discovered_at_turn', 1)}`",
        "---",
        "### 🔗 Relational Vectors"
    ]
    
    connections_count = 0
    for edge in graph.get("edges", []):
        if edge["source"] == entity_name:
            report.append(f"- Maps **{edge['relation']}** → **{edge['target']}** *(Turn #{edge['turn']})*")
            connections_count += 1
        elif edge["target"] == entity_name:
            report.append(f"- **{edge['source']}** → holds **{edge['relation']}** index context *(Turn #{edge['turn']})*")
            connections_count += 1
            
    if connections_count == 0:
        report.append("*No relational vectors mapped inside active Graphify context.*")
        
    return "\n".join(report)

# =========================================================================
# 🛰️ GRAPHIFY CONTINUUM ARCHIVAL LOGIC HANDLERS
# =========================================================================

async def run_ai_timeline_compression(session_user, api_key, selected_bundle):
    if not api_key:
        return "🚨 Authentication failure: You must paste an API key inside the studio input box to authenticate the agent!"
    
    from engine import call_google_engine, call_openai_engine, call_anthropic_engine, call_open_source_engine
    
    memory = GraphifyStoryMemory()
    bundle_config = engine.MODEL_BUNDLES.get(selected_bundle, list(engine.MODEL_BUNDLES.values())[0])
    
    provider = bundle_config["provider"]
    if provider == "google":
        router_fn = call_google_engine
    elif provider == "openai":
        router_fn = call_openai_engine
    elif provider == "anthropic":
        router_fn = call_anthropic_engine
    else:
        router_fn = call_open_source_engine
        
    try:
        await memory.compress_autonomous(session_user, api_key, router_fn, bundle_config)
        return "✅ AI Autonomous Timeline Synthesis complete! The history ledger has been compiled, compressed, and synchronized."
    except Exception as e:
        return f"❌ Chronology Synthesis failed: {str(e)}"

def populate_continuum_checkboxes(session_user):
    memory = GraphifyStoryMemory()
    graph = memory.load_graph(session_user)
    history = graph["metadata"].get("history_log", [])
    
    choices = []
    for h in history:
        choices.append((f"Turn #{h['turn']} | Blueprint: {h['blueprint'][:50]}...", str(h['turn'])))
        
    if not choices:
        return gr.update(choices=[("No active simulation turns detected under your core workspace.", "0")])
    return gr.update(choices=choices)

def run_manual_timeline_compression(session_user, selected_turns_list):
    if not selected_turns_list:
        return "🚨 Action locked: You must select at least 1 critical scene turn to preserve!"
        
    memory = GraphifyStoryMemory()
    
    try:
        int_turn_ids = [int(t) for t in selected_turns_list]
        memory.compress_manual(session_user, int_turn_ids)
        return f"✅ Curated Manual Archival complete! {len(int_turn_ids)} turns preserved in high-fidelity, and the backlog compiled into backing metadata."
    except Exception as e:
        return f"❌ Manual continuum preservation process crashed: {str(e)}"

# =========================================================================
# 📚 LEGACY LORE IMPORT BOOTSTRAPPING HANDLER
# =========================================================================

async def bootstrap_legacy_story(session_user, api_key, selected_bundle, legacy_text):
    """
    Parses legacy chapters to extract pre-existing world elements 
    and imports them directly into the Graphify memory environment as a baseline.
    """
    if not api_key:
        return "🚨 Authentication failure: An active API key is required to analyze legacy files!"
    if not legacy_text.strip():
        return "🚨 Input empty: Please paste your pre-written chapter drafts in the staging box."

    from engine import call_google_engine, call_openai_engine, call_anthropic_engine, call_open_source_engine
    
    bundle_config = engine.MODEL_BUNDLES.get(selected_bundle, list(engine.MODEL_BUNDLES.values())[0])
    provider = bundle_config["provider"]
    model_target = bundle_config["model"]

    system_instruction = (
        "You are an advanced narrative archeologist. Analyze the provided legacy chapters "
        "and extract: \n"
        "1. Characters (name, type='Character', status/description)\n"
        "2. Key Locations (name, type='Location', status/description)\n"
        "3. Key Artifacts/Concepts (name, type='Artifact' or 'Concept', status/description)\n"
        "4. Key Relationships/Links between them\n"
        "5. A concise chronological summary of events so far.\n\n"
        "Format your output strictly as a JSON object matching this schema, without markdown formatting outside the JSON:\n"
        "{\n"
        "  \"entities\": [{\"name\": \"Name\", \"type\": \"Character/Location/Artifact/Concept\", \"status\": \"Status/Desc\"}],\n"
        "  \"relationships\": [{\"source\": \"Name\", \"target\": \"Name\", \"relation\": \"Relation Detail\"}],\n"
        "  \"summary\": \"Detailed summary of plot events so far\"\n"
        "}"
    )

    prompt = f"Deconstruct and bootstrap these chapters into our active lore graph:\n\n{legacy_text}"

    try:
        if provider == "open_source":
            analysis, _ = await call_open_source_engine(api_key, bundle_config["endpoint"], model_target, system_instruction, prompt, 0.2)
        elif provider == "google":
            analysis = await call_google_engine(api_key, model_target, system_instruction, prompt, 0.2)
        elif provider == "openai":
            analysis = await call_openai_engine(api_key, model_target, system_instruction, prompt, 0.2)
        elif provider == "anthropic":
            analysis = await call_anthropic_engine(api_key, model_target, system_instruction, prompt, 0.2)

        json_match = re.search(r"\{.*\}", analysis, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(analysis)

        memory = GraphifyStoryMemory()
        graph = memory.load_graph(session_user)

        current_turn = 1
        graph["metadata"]["total_turns"] = current_turn
        graph["metadata"]["history_log"] = [{
            "turn": current_turn,
            "blueprint": "Legacy Chapters Baseline Synthesis",
            "summary": data.get("summary", "Imported legacy manuscript baseline.")
        }]

        # Inject newly discovered legacy entities
        for entity in data.get("entities", []):
            node_id = entity["name"].strip()
            if not node_id:
                continue
            graph["nodes"][node_id] = {
                "type": entity.get("type", "Concept"),
                "status": entity.get("status", "Active Legacy Context"),
                "discovered_at_turn": current_turn
            }

        # Inject relationships
        for rel in data.get("relationships", []):
            graph["edges"].append({
                "source": rel["source"].strip(),
                "target": rel["target"].strip(),
                "relation": rel["relation"].strip(),
                "turn": current_turn
            })

        # Save to memory instance database
        memory.save_graph(session_user, graph)

        # ==========================================
        # 📜 PERSIST ARCHIVE TO LEGACY DATASET VAULT
        # ==========================================
        try:
            legacy_payload = {
                "metadata": {
                    "source": "Legacy Migration Portal",
                    "session_user": session_user,
                    "timestamp": int(time.time())
                },
                "extracted_data": data,
                "raw_text": legacy_text
            }
            
            # Formulate tracking filename and write locally
            filename = f"{session_user}_archive_{int(time.time())}.legacy"
            local_path = os.path.join("vault_media", filename)
            
            with open(local_path, "w", encoding="utf-8") as f:
                json.dump(legacy_payload, f, indent=4)
                
            # Fire the automated multi-dataset uploader
            upload_vault_asset_to_hub(local_path)
            backup_msg = " Cloud routing matrix updated."
        except Exception as io_err:
            backup_msg = f" (Local cache established; cloud routing notice: {io_err})"

        return f"🎉 Bootstrapping complete! Extracted {len(data.get('entities', []))} world elements and {len(data.get('relationships', []))} active relationship vectors.{backup_msg} Navigate to the Graphify tab to interact with your new map!"

    except Exception as e:
        return f"❌ Parsing error: {str(e)}. Make sure your API license key is valid."
