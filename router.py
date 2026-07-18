# router.py
import httpx
import asyncio  # 👈 Added to handle waiting/sleeping between retries
import gradio as gr
from google import genai
from google.genai import types
from models import MODEL_BUNDLES

# ==========================================
# 🔐 REAL-TIME API KEY SIGNATURE VALIDATOR
# ==========================================
def identify_key_and_filter_bundles(api_key):
    """
    Analyzes token structural signatures in real-time, dynamically mapping keys
    to the exact bundle dictionary keys configured inside models.py.
    """
    if not api_key or not api_key.strip():
        return gr.update(choices=[], value=""), "🔴 Status: No Active Key Token Detected."
        
    token = api_key.strip()
    
    # 1. Catch OpenRouter Signatures FIRST (Prevents 'sk-' match conflict)
    if token.startswith("sk-or-"):
        target_provider = "open_source"
        status_msg = "环境/Status 职能: 🟢 Status: OpenRouter Token Detected. High-fidelity prose nodes loaded."
    
    # 2. Detect Anthropic / Claude Signatures
    elif token.startswith("sk-ant-"):
        target_provider = "anthropic"
        status_msg = "环境/Status 职能: 🟣 Anthropic API Verified. Claude Cluster Engaged."
        
    # 3. Detect Native OpenAI Signatures
    elif token.startswith("sk-"):
        target_provider = "openai"
        status_msg = "环境/Status 职能: 🔵 OpenAI Production API Verified."
        
    # 4. Detect Google Cloud / Gemini Signatures
    elif token.startswith("AIzaSy"):
        target_provider = "google"
        status_msg = "环境/Status 职能: 🟡 Google Vertex Core Verified."
        
    # 5. Enforce strict character length threshold for generic Open-Weights tokens
    elif len(token) >= 15:
        target_provider = "open_source"
        status_msg = "环境/Status 职能: 🟢 Status: Open-Weights Token Detected. High-fidelity prose nodes loaded."
        
    # 6. Buffering state while user is actively typing out their key string
    else:
        return gr.update(choices=[], value=""), "⚠️ Status: Parsing incoming security token pattern..."

    # Dynamically pull keys from MODEL_BUNDLES to guarantee an exact string match
    matched_choices = [name for name, cfg in MODEL_BUNDLES.items() if cfg.get("provider") == target_provider]
    
    if not matched_choices:
        return gr.update(choices=["No compatible bundle keys found"], value=""), f"⚠️ Token signature matched '{target_provider}', but no bundles match this provider in models.py."
        
    return gr.update(choices=matched_choices, value=matched_choices[0]), status_msg


# ==========================================
# 🛰️ ENGINE API CALL PORTS
# ==========================================
async def call_google_engine(api_key, model, system_instruction, prompt, temperature):
    try:
        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=temperature)
        response = await client.aio.models.generate_content(model=model, contents=prompt, config=config)
        return response.text
    except Exception as e:
        raise RuntimeError(f"Google GenAI Core Engine Error: {str(e)}")

async def call_openai_engine(api_key, model, system_instruction, prompt, temperature):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "temperature": temperature, "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": prompt}]}
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60.0)
        res_json = response.json()
        if response.status_code != 200 or "error" in res_json:
            err_msg = res_json.get("error", {}).get("message", "Unknown Endpoint Exception")
            raise ValueError(f"OpenAI Gateway Error (Status {response.status_code}): {err_msg}")
        return res_json["choices"][0]["message"]["content"]

async def call_anthropic_engine(api_key, model, system_instruction, prompt, temperature):
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    payload = {"model": model, "max_tokens": 4000, "temperature": temperature, "system": system_instruction, "messages": [{"role": "user", "content": prompt}]}
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=60.0)
        res_json = response.json()
        if response.status_code != 200 or "error" in res_json:
            err_msg = res_json.get("error", {}).get("message", "Unknown Endpoint Exception")
            raise ValueError(f"Anthropic Gateway Error (Status {response.status_code}): {err_msg}")
        return res_json["content"][0]["text"]

async def call_open_source_engine(api_key, endpoint, model, system_instruction, prompt, temperature):
    # ==========================================
    # 🔄 DYNAMIC OPENROUTER INTERCEPTOR
    # ==========================================
    if api_key.strip().startswith("sk-or-"):
        # Redirect Together endpoint to OpenRouter API seamlessly
        if "together" in endpoint.lower():
            endpoint = "https://openrouter.ai/api/v1/chat/completions"
            
            # Normalize model identifiers
            model_lower = model.lower()
            if "qwen" in model_lower:
                model = model_lower.replace("qwen2.5", "qwen-2.5").replace("qwen2", "qwen-2")
            elif "deepseek" in model_lower:
                if "v3" in model_lower:
                    model = "deepseek/deepseek-chat"
                elif "r1" in model_lower:
                    model = "deepseek/deepseek-r1"
            elif "llama-3" in model_lower:
                model = model_lower.replace("-turbo", "").replace("meta-llama/meta-", "meta-llama/")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # Optional metadata headers required by OpenRouter
    if "openrouter.ai" in endpoint:
        headers["HTTP-Referer"] = "https://github.com/Narrative-engine-labs"
        headers["X-Title"] = "Stratagem Workspace"
        
    payload = {"model": model, "temperature": temperature, "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": prompt}]}
    
    # Retry configuration variables
    max_retries = 3
    backoff_time = 2.0  # seconds
    
    for attempt in range(max_retries):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, headers=headers, json=payload, timeout=90.0)
                res_json = response.json()
                
                # Check if we were Rate-Limited (429)
                if response.status_code == 429:
                    # Check if the API specified a dynamic wait time, otherwise use our backoff
                    retry_after_header = response.headers.get("Retry-After")
                    sleep_duration = float(retry_after_header) if retry_after_header and retry_after_header.isdigit() else backoff_time
                    
                    if attempt < max_retries - 1:
                        print(f"⚠️ OpenRouter Rate Limited (429). Retrying in {sleep_duration}s... (Attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(sleep_duration)
                        backoff_time *= 2  # Double the wait time for the next round
                        continue
                    else:
                        raise ValueError("OpenRouter Rate Limit Exceeded (429): The free-tier route is temporarily overloaded. Please try again in 10-15 seconds.")
                
                # Handle other unexpected errors
                if response.status_code != 200 or "error" in res_json:
                    err_msg = res_json.get("error", {}).get("message", "Inference Node Unreachable")
                    raise ValueError(f"Open-Weights Node Error (Status {response.status_code}): {err_msg}")
                    
                content = res_json["choices"][0]["message"]["content"]
                usage = res_json.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
                return content, usage
                
            except httpx.RequestError as exc:
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff_time)
                    backoff_time *= 2
                    continue
                raise ValueError(f"Network Connection Failed: {str(exc)}")
                
