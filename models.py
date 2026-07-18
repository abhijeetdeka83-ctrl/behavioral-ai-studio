import os

DB_FILE = "narrative_history.db"
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_DATASET_ID = os.environ.get("HF_DATASET_ID")
SECRET_SALT = os.environ.get("SECRET_BOUNDARIES_SALT", "super_secret_fallback_phrase_99")
SECRET_BOUNDARIES = os.environ.get("STRUCTURAL_BOUNDARIES", "Error: Prompt constraints missing.")
SECRET_BYPASS_TOKEN = os.environ.get("URL_BYPASS_TOKEN", "alpha_access_2026")

MODEL_BUNDLES = {
    # --- PAID ENGINE PROVIDERS (ALWAYS ULTRA-STABLE) ---
    "1. Anthropic Vault (Claude 3.5 Sonnet)": {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "type": "paid",
        "tier": "🔴 Premium Prose Execution"
    },
    "2. OpenAI Sentinel (GPT-4o Rigid Logic)": {
        "provider": "openai",
        "model": "gpt-4o",
        "type": "paid",
        "tier": "🟠 High-Rigidity Logic Check"
    },
    "3. Google Masterpiece (Gemini 1.5 Pro)": {
        "provider": "google",
        "model": "gemini-1.5-pro",
        "type": "paid",
        "tier": "🔴 Deep Long-Context RAG"
    },
    
    # --- 🌌 ELITE LITERARY OPEN-SOURCE MODELS (ROUTED VIA OPENROUTER - NO QWEN / NO GEMMA) ---
    "4. DeepSeek V4 Pro (Frontier Enterprise Reasoning)": {
        "provider": "open_source",
        "model": "deepseek/deepseek-v4-pro",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "type": "open_source",
        "tier": "🟢 Elite MoE Orchestration Node"
    },
    "5. Llama 3.3 70B (State-of-the-Art Dialogue & Pace)": {
        "provider": "open_source",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "type": "open_source",
        "tier": "🟢 Industry Standard Literary Automation"
    },
    "6. Hermes 3 Llama 3.1 405B (Exceptional Creative Flow & Logic)": {
        "provider": "open_source",
        "model": "nousresearch/hermes-3-llama-3.1-405b:free",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "type": "open_source",
        "tier": "🟢 Uncensored Premium Prose Engine"
    },
    "7. NVIDIA Nemotron 3 Ultra (1M Context Frontier Reasoning)": {
        "provider": "open_source",
        "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "type": "open_source",
        "tier": "🟢 Mamba-Transformer Long-Context Node"
    },
    "8. NVIDIA Nemotron 3 Super (Fast Narrative Flow & Logic)": {
        "provider": "open_source",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "type": "open_source",
        "tier": "🟢 Highly-Optimized Accelerator Node"
    },
    "9. OpenAI GPT-OSS 20B (Ultra-Snappy Plot Structure Extraction)": {
        "provider": "open_source",
        "model": "openai/gpt-oss-20b:free",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "type": "open_source",
        "tier": "🟢 Lightning-Fast Structural Auditing"
    },
    "10. DeepSeek V4 Flash (Ultra-Snappy Structural Plotting)": {
        "provider": "open_source",
        "model": "deepseek/deepseek-v4-flash",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "type": "open_source",
        "tier": "🟢 High-Throughput Quick Node"
    }
}
