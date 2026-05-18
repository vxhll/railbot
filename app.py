
"""
app.py
Main Streamlit chat interface for the Indian Railways AI Assistant.
Run with: streamlit run app.py
"""

import streamlit as st
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from orchestrator import process_user_query
from logo import get_logo

# Load .env from same folder as app.py
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RailBot — Indian Railways Assistant",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {
    --railway-blue: #2a5298;
    --railway-orange: #f26522;
    --railway-green: #4caf50;
    --railway-light: #1e2a3a;
    --bg-main: #0e1117;
    --card-bg: #1a1f2e;
    --border: #2d3550;
    --text-primary: #f0f2f6;
    --text-secondary: #a0aabf;
    --success: #4caf50;
    --warning: #ff9800;
  }

  html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
  }

  /* Force all text to be visible */
  p, span, div, label, li, td, th, h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
  }

  /* Streamlit default overrides */
  .stApp {
    background-color: var(--bg-main) !important;
  }

  section[data-testid="stSidebar"] {
    background-color: #111827 !important;
  }

  section[data-testid="stSidebar"] * {
    color: #f0f2f6 !important;
  }

  /* Header */
  .rail-header {
    background: linear-gradient(135deg, var(--railway-blue) 0%, #0d2447 100%);
    color: white;
    padding: 20px 28px;
    border-radius: 16px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 24px rgba(26,58,107,0.18);
  }

  .rail-header h1 {
    margin: 0;
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -0.5px;
  }

  .rail-header p {
    margin: 4px 0 0;
    font-size: 0.85rem;
    opacity: 0.75;
    font-weight: 300;
  }

  /* Chat messages */
  .chat-user {
    background: var(--railway-blue);
    color: white;
    padding: 14px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px 60px;
    font-size: 0.92rem;
    line-height: 1.5;
    box-shadow: 0 2px 8px rgba(26,58,107,0.15);
  }

  .chat-bot {
    background: #1a2744 !important;
    color: #f0f2f6 !important;
    padding: 14px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 60px 8px 0;
    font-size: 0.92rem;
    line-height: 1.6;
    border: 1px solid #2d3a5e;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }

  .chat-bot * {
    color: #f0f2f6 !important;
  }

  .chat-bot pre, .chat-bot code {
    font-family: 'JetBrains Mono', monospace;
    background: #0d1b2a;
    border-radius: 6px;
    font-size: 0.82rem;
    color: #7dd3fc !important;
  }

  /* Avatar badges */
  .avatar-user {
    font-size: 1.4rem;
    float: right;
    margin-left: 10px;
  }
  .avatar-bot {
    font-size: 1.4rem;
    float: left;
    margin-right: 10px;
  }

  /* Intent badge */
  .intent-badge {
    display: inline-block;
    background: var(--railway-light);
    color: var(--railway-blue);
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.3px;
    margin-top: 6px;
    font-family: 'JetBrains Mono', monospace;
  }

  .demo-banner {
    background: #2a2000;
    border: 1px solid #f59e0b;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 0.82rem;
    color: #fcd34d !important;
    margin-bottom: 12px;
  }

  .demo-banner * {
    color: #fcd34d !important;
  }

  /* Sidebar styling */
  .sidebar-section {
    background: #1a2535 !important;
    border: 1px solid #2d3a55;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
    font-size: 0.84rem;
    color: #f0f2f6 !important;
  }

  .sidebar-section * {
    color: #f0f2f6 !important;
  }

  .sidebar-section h4 {
    font-size: 0.88rem;
    font-weight: 700;
    color: #7dd3fc !important;
    margin: 0 0 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .sidebar-section code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    background: rgba(125,211,252,0.15);
    padding: 2px 6px;
    border-radius: 4px;
    color: #7dd3fc !important;
  }

  /* Quick action chips */
  .stButton > button {
    font-family: 'Sora', sans-serif !important;
    font-size: 0.80rem !important;
    font-weight: 500 !important;
    border-radius: 20px !important;
    border: 1.5px solid #2d3a55 !important;
    background: #1a2535 !important;
    color: #a0c4ff !important;
    padding: 4px 14px !important;
    transition: all 0.18s ease !important;
  }
  .stButton > button:hover {
    border-color: #4a90d9 !important;
    background: #1e3050 !important;
    transform: translateY(-1px);
  }

  /* Input styling */
  .stTextInput > div > div > input {
    font-family: 'Sora', sans-serif !important;
    border-radius: 12px !important;
    border: 2px solid #2d3a55 !important;
    font-size: 0.92rem !important;
    padding: 12px 16px !important;
    background: #1a2535 !important;
    color: #f0f2f6 !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: #4a90d9 !important;
    box-shadow: 0 0 0 3px rgba(74,144,217,0.2) !important;
  }
  .stTextInput > div > div > input::placeholder {
    color: #6b7a99 !important;
  }

  /* Divider */
  hr {
    border: none;
    border-top: 1.5px solid var(--border);
    margin: 12px 0;
  }

  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # full chat history (user + assistant dicts)
if "chat_display" not in st.session_state:
    st.session_state.chat_display = []  # display items (text + intent)
if "pending_input" not in st.session_state:
    st.session_state.pending_input = ""

# Check API key config
anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
demo_mode = not bool(rapidapi_key)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 10px 0 16px;">
      {get_logo(80)}<br>
      <strong style="font-size:1.1rem; color:#7dd3fc;">RailBot</strong><br>
      <span style="font-size:0.75rem; color:#a0aabf;">Indian Railways AI Assistant</span>
    </div>
    """, unsafe_allow_html=True)

    # API Status
    st.markdown('<div class="sidebar-section"><h4>⚙️ API Status</h4>', unsafe_allow_html=True)
    st.markdown(
        f"{'✅' if anthropic_key else '❌'} **Anthropic Claude** — {'Connected' if anthropic_key else 'Missing key'}"
    )
    st.markdown(
        f"{'✅' if rapidapi_key else '🟡'} **RapidAPI Railways** — {'Connected' if rapidapi_key else 'Demo Mode'}"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Station codes reference
    st.markdown("""
    <div class="sidebar-section">
      <h4>🗺️ Station Codes</h4>
      <table style="width:100%; font-size:0.78rem; border-collapse:collapse;">
        <tr><td>New Delhi</td><td><code>NDLS</code></td></tr>
        <tr><td>Mumbai Central</td><td><code>BCT</code></td></tr>
        <tr><td>Mumbai CSMT</td><td><code>CSTM</code></td></tr>
        <tr><td>Howrah</td><td><code>HWH</code></td></tr>
        <tr><td>Chennai Central</td><td><code>MAS</code></td></tr>
        <tr><td>Bangalore</td><td><code>SBC</code></td></tr>
        <tr><td>Hyderabad</td><td><code>SC</code></td></tr>
        <tr><td>Pune</td><td><code>PUNE</code></td></tr>
        <tr><td>Ahmedabad</td><td><code>ADI</code></td></tr>
      </table>
    </div>
    """, unsafe_allow_html=True)

    # Tatkal timing guide
    st.markdown("""
    <div class="sidebar-section">
      <h4>⏰ Tatkal Windows</h4>
      <p style="margin:4px 0; font-size:0.80rem;">🔷 <strong>AC Classes</strong> (1A/2A/3A/CC/EC)<br>
      Opens 1 day prior at <strong>10:00 AM IST</strong></p>
      <p style="margin:4px 0; font-size:0.80rem;">🔶 <strong>Non-AC Classes</strong> (SL/2S)<br>
      Opens 1 day prior at <strong>11:00 AM IST</strong></p>
    </div>
    """, unsafe_allow_html=True)

    # Class codes
    st.markdown("""
    <div class="sidebar-section">
      <h4>🎫 Class Codes</h4>
      <span style="font-size:0.78rem; line-height:2;">
        <code>1A</code> First AC &nbsp;
        <code>2A</code> 2-Tier AC<br>
        <code>3A</code> 3-Tier AC &nbsp;
        <code>SL</code> Sleeper<br>
        <code>CC</code> Chair Car &nbsp;
        <code>EC</code> Exec Chair<br>
        <code>2S</code> Second Sitting
      </span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_display = []
        st.rerun()


# ── Main area ──────────────────────────────────────────────────────────────────

# Header
st.markdown(f"""
<div class="rail-header">
  {get_logo(55)}
  <div>
    <h1>RailBot — Indian Railways AI Assistant</h1>
    <p>Ask me about seat availability, Tatkal quota, PNR status, and train schedules</p>
  </div>
</div>
""", unsafe_allow_html=True)

# Demo mode banner
if demo_mode:
    st.markdown("""
    <div class="demo-banner">
      🟡 <strong>Demo Mode Active</strong> — Running with simulated train data. 
      Add your <strong>RAPIDAPI_KEY</strong> to <code>.env</code> to get real live data from Indian Railways.
    </div>
    """, unsafe_allow_html=True)

def handle_message(msg: str):
    """Process a user message through the full RAG pipeline."""
    if not msg.strip():
        return
    if not anthropic_key:
        st.error("❌ ANTHROPIC_API_KEY not set. Please add it to your .env file.")
        return
    st.session_state.chat_display.append({"role": "user", "content": msg})
    st.session_state.messages.append({"role": "user", "content": msg})
    with st.spinner("🔍 Looking up live train data…"):
        response_text, intent = process_user_query(msg, st.session_state.messages[:-1])
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.session_state.chat_display.append({
        "role": "assistant",
        "content": response_text,
        "intent": intent.get("intent", ""),
    })
    st.session_state.pending_input = ""

# Quick action chips
st.markdown("**💬 Try asking:**")
cols = st.columns(4)
quick_queries = [
    "Check seats on 12951 NDLS to BCT tomorrow in 3A",
    "PNR status for 1234567890",
    "Is Tatkal open for 3A class tomorrow?",
    "Trains from NDLS to BCT tomorrow",
]
for i, q in enumerate(quick_queries):
    if cols[i].button(q[:35] + "…", key=f"quick_{i}"):
        st.session_state.pending_input = q
        st.rerun()

st.markdown("---")

# Chat display
chat_container = st.container()
with chat_container:
    if not st.session_state.chat_display:
        st.markdown("""
        <div style="text-align:center; padding:40px 0; color:#9aa5c4;">
          <span style="font-size:3rem;">🚉</span><br>
          <p style="font-size:0.95rem; margin-top:12px;">
            Hello! I'm RailBot, your Indian Railways assistant.<br>
            Ask me about seat availability, Tatkal quotas, PNR status, or train schedules.
          </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for item in st.session_state.chat_display:
            if item["role"] == "user":
                st.markdown(f"""
                <div class="chat-user">
                  <span class="avatar-user">👤</span>
                  {item["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                intent_label = item.get("intent", "")
                intent_html = f'<br><span class="intent-badge">intent: {intent_label}</span>' if intent_label and intent_label not in ("unknown", "general_question") else ""
                st.markdown(f'<div class="chat-bot"><span class="avatar-bot">🚆</span>{intent_html}</div>', unsafe_allow_html=True)
                st.markdown(item["content"])


# ── Input bar ──────────────────────────────────────────────────────────────────
st.markdown("---")

with st.form(key="chat_form", clear_on_submit=True):
    input_col, btn_col = st.columns([8, 1])
    user_input = input_col.text_input(
        label="Message",
        placeholder="Ask about seat availability, PNR status, or Tatkal quota…",
        value=st.session_state.pending_input,
        label_visibility="collapsed",
    )
    submitted = btn_col.form_submit_button("Send ➤", use_container_width=True)

# Handle quick button or form submission
if st.session_state.pending_input and not submitted:
    q = st.session_state.pending_input
    st.session_state.pending_input = ""
    handle_message(q)
    st.rerun()

if submitted and user_input:
    handle_message(user_input)
    st.rerun()

# Footer
st.markdown("""
<div style="text-align:center; margin-top:24px; color:#9aa5c4; font-size:0.75rem;">
  RailBot v1.0 · Powered by Claude AI + Indian Railways API · Data is for reference only
</div>
""", unsafe_allow_html=True)
