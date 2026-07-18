# ui_styles.py
CUSTOM_CSS = """
/* ==========================================
   🌌 GLOBAL ROOT THEME VARIABLES
   ========================================== */
:root {
    --body-background-fill: #050608 !important;
    --background-fill-primary: #0f111a !important;
    --background-fill-secondary: #090d16 !important;
    --border-color-primary: #1e293b !important;
    --block-background-fill: #090d16 !important;
    --block-border-color: #1e293b !important;
    --input-background-fill: #04060a !important;
    --input-border-color: #1e293b !important;
    --input-text-color: #ffffff !important;
    --body-text-color: #ffffff !important;
}

/* ==========================================
   🖥️ DESKTOP ENGINE FORCED CORE CONTAINER
   ========================================== */
body, .gradio-container {
    background: radial-gradient(circle at top center, #0f111a 0%, #050608 100%) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: #ffffff !important;
    max-width: 1400px !important;
    min-width: 1024px !important; /* Locks out mobile layout shrinking architectures */
    margin: 20px auto !important;
    padding: 24px !important;
    border: 1px solid #1e293b !important;
    border-radius: 16px !important;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.8) !important;
}

/* ==========================================
   🧱 FOOLPROOF CONTAINER & BOX OVERRIDES
   ========================================== */
/* Targets every single internal Gradio row, form group, and block container 
   to completely eliminate light fallback white-out boxes */
.workspace-card, .landing-container, .header-container, 
.block, .form, .row, .gr-form, .gr-box, .fieldset {
    background: #090d16 !important;
    background-color: #090d16 !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    box-sizing: border-box !important;
}

.header-container {
    background: transparent !important;
    border-bottom: 1px solid #1e293b !important;
    margin: 10px auto !important;
    padding: 24px !important;
}

.workspace-card, .landing-container {
    margin: 10px auto !important;
    padding: 24px !important;
}

p, h1, h2, h3, h4, span, label, 
.prose, .prose *, 
.markdown-text, .markdown-text * {
    color: #ffffff !important;
    word-wrap: break-word !important;
}

.brand-title h1 {
    font-size: 2.2rem !important;
    text-align: left !important;
    font-weight: 900 !important;
    letter-spacing: -0.03em !important;
    background: linear-gradient(135deg, #a78bfa 0%, #6366f1 50%, #38bdf8 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    line-height: 1.3 !important;
}

.tabitem {
    background: transparent !important;
    border: none !important;
}

/* ==========================================
   🔒 COMPONENT FIELD MATRIX
   ========================================== */
textarea, input[type="text"], input[type="password"], .gr-dropdown, select,
.gradio-textbox textarea, .gradio-dropdown select, .gradio-number input,
[data-testid="textbox"] textarea, .single-select {
    background: #04060a !important;
    background-color: #04060a !important;
    border: 1px solid #1e293b !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    width: 100% !important;
}

textarea:focus, input:focus, select:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    outline: none !important;
}

.manuscript-canvas textarea {
    font-family: "Georgia", serif !important;
    font-size: 1.1rem !important;
    line-height: 1.8 !important;
    background: #0b0f19 !important;
    padding: 24px !important;
}

/* ==========================================
   🗂️ DESKTOP TAB NAVIGATION SYSTEM
   ========================================== */
.tabs-navigation {
    display: flex !important;
    flex-direction: column !important; 
    margin-bottom: 20px !important;
}

.tabs-navigation > div:first-child {
    display: flex !important;
    flex-direction: row !important;
    border-bottom: 1px solid #1e293b !important;
}

.tabs-navigation button.tab-nav {
    width: auto !important;
    border-bottom: none !important;
    padding: 12px 24px !important;
    background: transparent !important;
    color: #cbd5e1 !important;
}

.tabs-navigation button.tab-nav.selected {
    border-left: none !important;
    border-bottom: 2px solid #a78bfa !important;
    color: #a78bfa !important;
}

/* ==========================================
   ⚙️ INTERACTION BUTTONS & BADGES
   ========================================== */
.action-btn {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    padding: 14px !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    width: 100% !important;
}

.secondary-btn {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #cbd5e1 !important;
}

.status-badge {
    background: #04060a !important;
    border: 1px solid #1e293b !important;
    padding: 10px 14px !important;
    border-radius: 6px !important;
    font-size: 0.88rem !important;
    display: block;
}

/* ==========================================
   ⚡ PRODUCTION ENGINE TELEMETRY PATCHES
   ========================================== */
.wrap.loading {
    background: rgba(5, 6, 8, 0.92) !important;
}
.wrap.loading .progress-text,
.wrap.loading .eta-bar,
.wrap.loading .duration,
.loading-box,
.eta-display,
div[class*="loading"] text {
    color: #a78bfa !important;
    font-weight: 800 !important;
    font-family: monospace !important;
    font-size: 1.1rem !important;
    text-shadow: 0 0 10px rgba(167, 139, 250, 0.4) !important;
}
.progress-container, .progress-bar {
    background-color: #1e293b !important;
}

.kpi-container {
    display: flex !important;
    flex-direction: column !important;
    gap: 1.25rem !important;
    background: #04060a !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    padding: 12px !important;
}

textarea[placeholder*="Telemetry operational metrics"],
.kpi-container textarea, 
div[class*="textbox"] textarea {
    font-family: 'Fira Code', 'Courier New', monospace !important;
    font-size: 0.9rem !important;
    line-height: 1.5 !important;
    background: #030508 !important;
    color: #38bdf8 !important;
}
"""
