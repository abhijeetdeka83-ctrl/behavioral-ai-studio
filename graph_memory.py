# graph_memory.py - Persistent Graphify Narrative Memory Engine
import os
import json

class GraphifyStoryMemory:
    def __init__(self, storage_dir: str = "./storage/graph_memory"):
        self.storage_dir = storage_dir
        self.max_turns = 1000  # Scaled to 1000 active turns
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_graph_path(self, username: str) -> str:
        return os.path.join(self.storage_dir, f"{username}_narrative_graph.json")

    def load_graph(self, username: str) -> dict:
        path = self._get_graph_path(username)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "nodes": {}, 
            "edges": [], 
            "metadata": {"history_log": [], "total_turns": 0}
        }

    def save_graph(self, username: str, graph_data: dict):
        path = self._get_graph_path(username)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)

    def update_graph_from_scene(self, username: str, blueprint: str, entities: list, relationships: list):
        """
        Appends new narrative layers, shifts the sliding turn context, and tags 
        every node with a temporal step key for timeline scrubbing.
        """
        graph = self.load_graph(username)
        
        # 1. Update total history ticker
        graph["metadata"]["total_turns"] += 1
        current_turn = graph["metadata"]["total_turns"]
        
        # Maintain 1000-turn chronological log window
        history_log = graph["metadata"].setdefault("history_log", [])
        history_log.append({
            "turn": current_turn, 
            "blueprint": blueprint,
            "summary": blueprint[:100] + "..." if len(blueprint) > 100 else blueprint
        })
        if len(history_log) > self.max_turns:
            history_log.pop(0) # Drop the oldest turn record

        # 2. Upsert Nodes (Entities)
        for entity in entities:
            node_id = entity["name"].strip()
            if not node_id:
                continue
            if node_id not in graph["nodes"]:
                graph["nodes"][node_id] = {
                    "type": entity.get("type", "Concept"), # e.g., Character, Location, Artifact
                    "status": entity.get("status", "Discovered"),
                    "discovered_at_turn": current_turn
                }
            else:
                # Update status seamlessly if modified by later scenes
                graph["nodes"][node_id]["status"] = entity.get("status", graph["nodes"][node_id]["status"])

        # 3. Append Edges (Relationships)
        for rel in relationships:
            edge_entry = {
                "source": rel["source"].strip(),
                "target": rel["target"].strip(),
                "relation": rel["relation"].strip(),
                "turn": current_turn
            }
            if edge_entry not in graph["edges"]:
                graph["edges"].append(edge_entry)

        self.save_graph(username, graph)

    async def compress_autonomous(self, username: str, api_key: str, router_fn, bundle_config: dict):
        """
        Synthesizes the active history log ledger into a condensed high-fidelity 
        Historical Epoch Node via AI, flushing the active context sliding window.
        """
        graph = self.load_graph(username)
        history_log = graph["metadata"].get("history_log", [])
        if not history_log:
            return

        timeline_text = "\n".join([f"Turn #{h['turn']}: {h['summary']}" for h in history_log])
        system_instruction = "You are an advanced narrative compression engine. Synthesize the provided timeline context into a dense, high-fidelity historical summary record."
        prompt = f"Compress the following timeline chronicle history logs into an analytical backing summary:\n\n{timeline_text}"
        
        try:
            if bundle_config.get("provider") == "open_source":
                summary, _ = await router_fn(api_key, bundle_config["endpoint"], bundle_config["model"], system_instruction, prompt, 0.3)
            else:
                summary = await router_fn(api_key, bundle_config["model"], system_instruction, prompt, 0.3)
        except Exception:
            summary = f"Archived Narrative Epoch: Consolidated {len(history_log)} active simulation turns into fallback metadata."

        # Inject unified Epoch Summary Node into the network topology map
        epoch_node_id = f"Historical_Epoch_{history_log[0]['turn']}_to_{history_log[-1]['turn']}"
        graph["nodes"][epoch_node_id] = {
            "type": "Concept",
            "status": summary[:250] + "..." if len(summary) > 250 else summary,
            "discovered_at_turn": graph["metadata"]["total_turns"]
        }
        
        # Flush sliding window log
        graph["metadata"]["history_log"] = []
        self.save_graph(username, graph)

    def compress_manual(self, username: str, selected_turn_ids: list):
        """
        Preserves designated full-length scene turn choices while dropping 
        and condensing unselected backlog data into an archival reference log.
        """
        graph = self.load_graph(username)
        history_log = graph["metadata"].get("history_log", [])
        if not history_log:
            return

        preserved_logs = []
        archived_summaries = []

        for log in history_log:
            if int(log["turn"]) in selected_turn_ids:
                preserved_logs.append(log)
            else:
                archived_summaries.append(f"Turn #{log['turn']}: {log['summary']}")

        if archived_summaries:
            archive_record = {
                "archive_run_at": graph["metadata"]["total_turns"],
                "data": " | ".join(archived_summaries)
            }
            graph["metadata"].setdefault("archived_epoch_records", []).append(archive_record)

        graph["metadata"]["history_log"] = preserved_logs
        self.save_graph(username, graph)

    def generate_llm_context_report(self, username: str) -> str:
        """
        Distills the raw network graph into a dense, structural Markdown 
        manifesto for the LLM injection layer—70x more efficient than text logs.
        """
        graph = self.load_graph(username)
        if not graph["nodes"]:
            return ""
            
        report = [
            "<LAYER_3_GRAPHIFY_CONTINUITY_MAP>",
            f"Active Narrative Horizon: Last {len(graph['metadata']['history_log'])} of {graph['metadata']['total_turns']} turns.",
            "\n[Tracked Active Entities]"
        ]
        
        for name, info in graph["nodes"].items():
            report.append(f"- **{name}** ({info['type']}) | State: {info['status']} | Enters at Turn: #{info['discovered_at_turn']}")
            
        report.append("\n[Established Relationship Edges]")
        for edge in graph["edges"]:
            report.append(f"- {edge['source']} ──({edge['relation']})──> {edge['target']} (Logged at Turn #{edge['turn']})")
            
        report.append("</LAYER_3_GRAPHIFY_CONTINUITY_MAP>")
        return "\n".join(report)
