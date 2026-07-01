import os
import re
import math
import zipfile
import xml.etree.ElementTree as ET
import time  # ⏱️ Native timestamp clock tracking for memory pruning

class LoreMapRAG:
    """Handles in-memory text chunking, indexing, and semantic retrieval for a single user context."""
    def __init__(self, chunk_size=1200, chunk_overlap=300):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks = []
        self.index = {}
        self.source_filename = "unknown_source"

    def _clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _tokenize(self, text):
        return re.findall(r'\b\w+\b', text.lower())

    def _extract_docx_text(self, file_path):
        """Pure-Python zero-dependency .docx text extractor parsing internal XML tags."""
        try:
            with zipfile.ZipFile(file_path) as docx:
                xml_content = docx.read('word/document.xml')
                root = ET.fromstring(xml_content)
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                text_pieces = []
                for paragraph in root.iter('{############}p'.replace('############', ns['w'])):
                    p_text = "".join([node.text for node in paragraph.iter('{############}t'.replace('############', ns['w'])) if node.text])
                    if p_text:
                        text_pieces.append(p_text)
                return "\n".join(text_pieces)
        except Exception as e:
            raise ValueError(f"DOCX extraction fault: {str(e)}")

    def _extract_pdf_fallback(self, file_path):
        """Gracefully sanitizes and extracts legible text strings out of basic layout streams."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            strings = re.findall(b'[(](.*?)[)]', content)
            text = " ".join([s.decode('utf-8', errors='ignore') for s in strings if len(s) > 3])
            if not text.strip():
                text = re.sub(r'[^\x20-\x7E\n]', '', content.decode('utf-8', errors='ignore'))
            return text
        except Exception as e:
            raise ValueError(f"PDF extraction fault: {str(e)}")

    def load_and_chunk_file(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return False, "[RAG ERROR] Targeted target asset file path does not exist."
            
        self.source_filename = os.path.basename(file_path)
        _, ext = os.path.splitext(self.source_filename.lower())
        
        try:
            if ext in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
            elif ext == '.docx':
                raw_text = self._extract_docx_text(file_path)
            elif ext == '.pdf':
                raw_text = self._extract_pdf_fallback(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_text = f.read()

            cleaned_text = self._clean_text(raw_text)
            if not cleaned_text or len(cleaned_text.strip()) < 10:
                return False, f"[RAG WARN] Extracted payload from '{self.source_filename}' contains insufficient character density."

            self.chunks = []
            start = 0
            while start < len(cleaned_text):
                end = start + self.chunk_size
                if end < len(cleaned_text):
                    last_space = cleaned_text.rfind(' ', start, end)
                    if last_space > start:
                        end = last_space
                
                chunk = cleaned_text[start:end].strip()
                if chunk:
                    self.chunks.append(chunk)
                start += (self.chunk_size - self.chunk_overlap)
                
            self._build_inverted_index()
            return True, f"[RAG SUCCESS] Resource '{self.source_filename}' successfully mapped into {len(self.chunks)} isolated tracking vectors."
        except Exception as e:
            return False, f"[RAG ENGINE FAULT] Extraction structural crash: {str(e)}"

    def _build_inverted_index(self):
        self.index = {}
        for chunk_idx, chunk in enumerate(self.chunks):
            tokens = self._tokenize(chunk)
            for token in tokens:
                if token not in self.index:
                    self.index[token] = {}
                self.index[token][chunk_idx] = self.index[token].get(chunk_idx, 0) + 1

    def retrieve_context_with_logs(self, blueprint_query, top_k=3):
        telemetry_log = f"[RAG TELEMETRY] Initiating text vector search against source: '{self.source_filename}'\n"
        if not self.chunks:
            telemetry_log += "[RAG TELEMETRY] Lore storage manifest is empty. Bypassing context injection.\n"
            return "", telemetry_log

        if not blueprint_query or len(blueprint_query.strip()) < 3:
            telemetry_log += "[RAG TELEMETRY] Blueprint prompt query length is too shallow. Returning base top_k blocks.\n"
            fallback_context = "\n\n---\n\n".join(self.chunks[:top_k])
            return fallback_context, telemetry_log

        query_tokens = self._tokenize(blueprint_query)
        scores = {}
        for token in query_tokens:
            if token in self.index:
                match_dict = self.index[token]
                idf = math.log(1.0 + (len(self.chunks) / (1.0 + len(match_dict))))
                for chunk_idx, term_freq in match_dict.items():
                    scores[chunk_idx] = scores.get(chunk_idx, 0.0) + (term_freq * idf)

        if not scores:
            telemetry_log += "[RAG TELEMETRY] 0 explicit token matches identified. Falling back to primary sequence blocks.\n"
            fallback_context = "\n\n---\n\n".join(self.chunks[:top_k])
            return fallback_context, telemetry_log

        sorted_chunks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, score in sorted_chunks[:top_k]]
        
        telemetry_log += f"[RAG TELEMETRY] Evaluated query matches across indices. Top relevance matrices:\n"
        for rank, (idx, score) in enumerate(sorted_chunks[:top_k]):
            telemetry_log += f"  ├── Vector Rank #{rank+1} -> Chunk Segment #{idx} (Matching Weight Score: {round(score, 4)})\n"
        
        retrieved_blocks = [self.chunks[i] for i in top_indices]
        context_string = "\n\n[Injected Core Lore Context Chunks]\n" + "\n\n---\n\n".join(retrieved_blocks)
        telemetry_log += f"[RAG TELEMETRY] Injected {len(retrieved_blocks)} optimized context blocks into compilation stack payload."
        return context_string, telemetry_log


# =====================================================================
# 🛡️ UPGRADED: CONCURRENCY STATE MANAGER WITH LRU MEMORY EVICTION
# =====================================================================
class SessionRAGManager:
    """Orchestrates multiple sandboxed RAG tracking spaces with an automated LRU memory eviction engine."""
    def __init__(self, max_sessions=20):
        self.user_sessions = {}
        self.last_active = {}       # ⏱️ Tracks high-precision Unix epoch heartbeats per user session
        self.max_sessions = max_sessions

    def _get_user_engine(self, username):
        """Fetches or instantiates a user's context sandbox, automatically enforcing global memory limits."""
        clean_user = username if username else "anonymous_node"
        current_time = time.time()
        
        # If allocation is brand new, verify cluster threshold constraints before writing to memory
        if clean_user not in self.user_sessions:
            if len(self.user_sessions) >= self.max_sessions:
                self._evict_oldest_session()
            self.user_sessions[clean_user] = LoreMapRAG()
            
        # Register fresh heartbeat trace activity
        self.last_active[clean_user] = current_time
        return self.user_sessions[clean_user]

    def _evict_oldest_session(self):
        """Identifies and purges the oldest, least recently used vector pool to protect the server RAM footprint."""
        if not self.last_active:
            return
            
        # Target the session entry matching the minimum active epoch timestamp
        oldest_user = min(self.last_active, key=self.last_active.get)
        print(f"⚠️ [MEMORY WARDEN] Total active workspaces >= threshold ({self.max_sessions}).")
        print(f"   └── Evicting stale context arrays for user session: '{oldest_user}' to secure RAM headroom.")
        
        # Pop keys from tracking storage tables, forcing Python's garbage collector to destroy data structures
        self.user_sessions.pop(oldest_user, None)
        self.last_active.pop(oldest_user, None)

    def ingest_user_asset(self, username, file_path):
        """Routes file indexing process to the specific user's isolated object sandbox instance."""
        user_engine = self._get_user_engine(username)
        success, log_msg = user_engine.load_and_chunk_file(file_path)
        return success, log_msg

    def retrieve_user_context(self, username, blueprint_query, top_k=3):
        """Extracts context and telemetry exclusively from the target user's isolated data repository."""
        user_engine = self._get_user_engine(username)
        return user_engine.retrieve_context_with_logs(blueprint_query, top_k=top_k)
        
