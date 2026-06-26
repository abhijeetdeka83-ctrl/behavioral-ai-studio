import os
import datetime
import hashlib
import gradio as gr
from google import genai
from google.genai import types

# 🔒 FETCH THE SECRET SALT FROM YOUR SETTINGS VAULT
# Change this secret word in your Hugging Face Settings -> Variables and Secrets
SECRET_SALT = os.environ.get("SECRET_BOUNDARIES_SALT", "super_secret_fallback_phrase_99")
SECRET_BOUNDARIES = os.environ.get("STRUCTURAL_BOUNDARIES", "Error: Prompt constraints missing.")

def generate_story(buyer_api_key, plot_outline):
    if not buyer_api_key.strip() or not plot_outline.strip():
        return "🚨 Please fill out both fields!"
    try:
        client = genai.Client(api_key=buyer_api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Write a scene based on this outline: {plot_outline}",
            config=types.GenerateContentConfig(
                system_instruction=SECRET_BOUNDARIES,
                temperature=0.75
            )
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# 🔐 THE ALGORITHMIC GATEKEEPER
def verify_license_key(username, password):
    username_clean = username.lower().strip()
    password_clean = password.strip()
    
    if "-" not in password_clean:
        return False
        
    try:
        # Split the password into the Expiration Date and the Math Signature
        expiry_str, client_signature = password_clean.split("-", 1)
        
        # 1. TIME CHECK: Has the license expired?
        expiry_date = datetime.datetime.strptime(expiry_str, "%Y%m%d").date()
        if datetime.date.today() > expiry_date:
            return False # Access Denied: Key expired
            
        # 2. MATH CHECK: Re-generate the signature to see if it matches
        # Combines username + expiry date + your hidden secret word
        raw_string = f"{username_clean}{expiry_str}{SECRET_SALT}"
        expected_signature = hashlib.sha256(raw_string.encode()).hexdigest()[:6]
        
        # If the math matches, let them in!
        return client_signature == expected_signature
        
    except Exception:
        return False

# UI LAYOUT
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎭 Elite Behavioral Narrative Engine")
    with gr.Row():
        with gr.Column():
            api_input = gr.Textbox(label="🔑 Gemini API Key", type="password")
            outline_input = gr.Textbox(label="📝 Plot Outline", lines=5)
            submit_btn = gr.Button("⚡ Compile Prose Tokens", variant="primary")
        with gr.Column():
            output_text = gr.Textbox(label="✨ Output", lines=12)
            
    submit_btn.click(fn=generate_story, inputs=[api_input, outline_input], outputs=output_text)

# LAUNCH WITH LOCKSCREEN ENABLED
demo.launch(auth=verify_license_key, auth_message="Enter your custom Discord username and License Password.")
