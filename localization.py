# localization.py
# Macro-National Language Configuration Matrix for Stratagem Workspace
from google import genai
from google.genai import types

TARGET_LANGUAGES = {
    "English": "English",
    "Mandarin Chinese (简体中文)": "Mandarin Chinese (Simplified)",
    "Hindi (हिन्दी)": "Hindi",
    "Spanish (Español)": "Spanish",
    "French (Français)": "French",
    "Arabic (العربية)": "Modern Standard Arabic",
    "Russian (Русский)": "Russian",
    "Portuguese (Português)": "Portuguese",
    "Indonesian (Bahasa Indonesia)": "Indonesian",
    "German (Deutsch)": "German",
    "Japanese (日本語)": "Japanese",
    "Turkish (Türkçe)": "Turkish",
    "Vietnamese (Tiếng Việt)": "Vietnamese",
    "Tagalog / Filipino (Wikang Tagalog)": "Tagalog (Filipino)",
    "Korean (한국어)": "Korean",
    "Farsi / Persian (فارسی)": "Farsi (Persian)",
    "Italian (Italiano)": "Italian",
    "Polish (Polski)": "Polish",
    "Thai (ภาษาไทย)": "Thai",
    "Ukrainian (Українська)": "Ukrainian"
}

def translate_manuscript(compiled_text, selected_language, api_token):
    """
    Leverages your modern Gemini setup to dynamically translate the compiled 
    manuscript into the selected national macro-language.
    """
    # Validation safety boundaries
    if not compiled_text or "System idle" in compiled_text:
        return "⚠️ Clear text layout error: No compiled manuscript detected to translate."
        
    if not api_token:
        return "🔑 Missing Token: Please provide a valid Gemini Developer Token to run translation."

    # Map the UI selection back to the clean prompt instruction string
    target_lang = TARGET_LANGUAGES.get(selected_language, "English")
    
    try:
        # Initialize using the modern unified SDK format to match engine.py
        client = genai.Client(api_key=api_token)
        
        prompt = f"""
        You are an elite enterprise localization system. 
        Translate the following manuscript text precisely into fluent, natural, national-level {target_lang}.
        Preserve all narrative pacing, structural markdown layouts, dialogue tone, and punctuation configurations exactly.
        
        Text to translate:
        {compiled_text}
        """
        
        # Execute content compilation via the standardized client wrapper
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        return response.text
        
    except Exception as e:
        return f"❌ Localization Engine Fault: {str(e)}"
        
