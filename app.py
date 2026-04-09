import streamlit as st
import streamlit.components.v1 as components
import requests
import datetime
import pytz
from cryptography.fernet import Fernet
import base64

# --- 1. SECURITY CONFIG ---
# Replace this with your own secret key. 
# You can generate a new one using Fernet.generate_key()
SECRET_KEY = b'v-9_Exam_Security_Key_2026_Stay_Safe_Always=' 
cipher_suite = Fernet(SECRET_KEY)

def encrypt_token(plain_text):
    return cipher_suite.encrypt(plain_text.encode()).decode()

def decrypt_token(token):
    try:
        return cipher_suite.decrypt(token.encode()).decode()
    except:
        return None

# --- 2. CONFIG & DUAL-PANE FIX ---
st.set_page_config(page_title="Exam Portal", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { overflow: hidden; height: 100vh; }
    [data-testid="stMainViewContainer"] { height: 100vh; }
    [data-testid="column"]:nth-child(1) { height: 95vh; overflow-y: auto; padding-right: 15px; }
    [data-testid="column"]:nth-child(2) { height: 95vh; overflow: hidden; display: flex; flex-direction: column; }
    [data-testid="column"]:nth-child(1)::-webkit-scrollbar { width: 8px; }
    [data-testid="column"]:nth-child(1)::-webkit-scrollbar-thumb { background: #cbd5e0; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

params = st.query_params

# --- 3. DATA PARSING (Handles both Encrypted & Old Links) ---
config = None

if "token" in params:
    # New Secure Method
    decoded_str = decrypt_token(params.get("token"))
    if decoded_str:
        parts = decoded_str.split("|")
        config = {
            "form": parts[0], "hook": parts[1], "until": parts[2],
            "ref": parts[3], "tool": parts[4]
        }
    else:
        st.error("🚫 Invalid or corrupted secure link.")
        st.stop()
elif "form" in params:
    # Fallback for old legacy links
    config = {
        "form": params.get("form"),
        "hook": params.get("hook"),
        "until": params.get("until"),
        "ref": params.get("ref"),
        "tool": params.get("tool")
    }

# --- 4. EXPIRATION CHECK ---
if config and config.get("until") != "None":
    try:
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now = datetime.datetime.now(vn_tz)
        u = config["until"]
        deadline = vn_tz.localize(datetime.datetime(
            int(u[:4]), int(u[4:6]), int(u[6:8]), 
            int(u[8:10]), int(u[10:12])
        ))
        if now > deadline:
            st.error(f"🚫 This portal closed on {deadline.strftime('%b %d, %Y at %H:%M')}.")
            st.stop()
    except: pass

def send_log(url, name, action):
    try: requests.post(url, json={"name": name, "action": action}, timeout=5)
    except: pass

# --- 5. STUDENT MODE ---
if config:
    if 'has_started' not in st.session_state: st.session_state.has_started = False
    if 'is_active' not in st.session_state: st.session_state.is_active = True

    c1, c2 = st.columns([7, 3])
    
    with c1: 
        st.title("📝 Online Examination")
        if st.session_state.has_started:
            tab_map = {"✍️ Assignment": config['form']}
            if config['ref'] and config['ref'] != "None": tab_map["📋 Resources"] = config['ref']
            if config['tool'] and config['tool'] != "None": tab_map["🔍 Tools"] = config['tool']

            tabs = st.tabs(list(tab_map.keys()))
            for i, (name, url) in enumerate(tab_map.items()):
                with tabs[i]:
                    st.markdown(f'<iframe src="{url}" width="100%" height="1500px" style="border:none;"></iframe>', unsafe_allow_html=True)
    
    with c2:
        st.write("---")
        if not st.session_state.has_started:
            with st.form("start"):
                s_name = st.text_input("Candidate Name:", placeholder="Enter full name")
                if st.form_submit_button("🚀 START EXAM", use_container_width=True):
                    if s_name:
                        st.session_state.student_name = s_name
                        st.session_state.has_started = True
                        send_log(config['hook'], s_name, "START")
                        st.rerun()
        else:
            st.info(f"👤 Candidate: **{st.session_state.student_name}**")
            if st.session_state.is_active:
                if st.button("🏁 FINISH", type="primary", use_container_width=True):
                    send_log(config['hook'], st.session_state.student_name, "FINISH")
                    st.session_state.is_active = False
                    st.toast("Submission logged.")
            if not st.session_state.is_active:
                st.success("✅ Exam is finished.")

    if st.session_state.has_started and st.session_state.is_active:
        components.html(f"""
            <script>
            document.addEventListener("visibilitychange", function() {{
                if (document.hidden) {{
                    fetch('{config['hook']}', {{
                        method: 'POST', mode: 'no-cors',
                        body: JSON.stringify({{ name: '{st.session_state.student_name}', action: 'LEAVE TAB' }})
                    }});
                }}
            }});
            </script>
        """, height=0)

# --- 6. TEACHER MODE ---
else:
    st.title("🛠️ Exam Management Console")
    t_setup, t_gen = st.tabs(["📖 Setup Guide", "🚀 Generate Exam Link"])
    
    with t_setup:
        # (Instructions remains the same as your previous code)
        st.markdown("### Phase 1: Google Sheets Setup")
        st.code("""/* (Apps Script Code from your original post) */""", language="javascript")
        
    with t_gen:
        with st.form("generator"):
            h = st.text_input("Webhook URL (from Apps Script):")
            f = st.text_input("Google Form Link:")
            r = st.text_input("Resource Link (Optional):", value="None")
            t = st.text_input("Tool Link (Optional):", value="None")
            st.write("---")
            st.subheader("⚙️ Expiration Settings")
            col1, col2 = st.columns(2)
            with col1: exp_date = st.date_input("Lock Date:")
            with col2: exp_time = st.time_input("Lock Time:")
            
            if st.form_submit_button("GENERATE SECURE LINK", use_container_width=True):
                if h and f:
                    u_param = f"{exp_date.strftime('%Y%m%d')}{exp_time.strftime('%H%M')}" if exp_time else "None"
                    
                    # ENCRYPTION LOGIC
                    raw_data = f"{f}|{h}|{u_param}|{r}|{t}"
                    token = encrypt_token(raw_data)
                    
                    base_url = "https://online-exam.streamlit.app/" 
                    secure_link = f"{base_url}?token={token}"
                    
                    st.success("Secure Link Generated!")
                    st.code(secure_link)
                else:
                    st.error("Webhook and Form links are mandatory.")
