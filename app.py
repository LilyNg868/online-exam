import streamlit as st
import streamlit.components.v1 as components
import requests
import datetime
import pytz

# --- 1. CONFIG & LOCK LOGIC ---
st.set_page_config(page_title="Exam Portal", layout="wide")
params = st.query_params

# Automatic Expiration Check
if "until" in params and params.get("until") != "None":
    try:
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now = datetime.datetime.now(vn_tz)
        u = params.get("until") # Expected format: YYYYMMDDHHmm
        
        deadline = vn_tz.localize(datetime.datetime(
            int(u[:4]), int(u[4:6]), int(u[6:8]), 
            int(u[8:10]), int(u[10:12])
        ))
        
        if now > deadline:
            st.error(f"🚫 This portal closed on {deadline.strftime('%b %d, %Y at %H:%M')}.")
            st.info("Submissions are no longer accepted for this session.")
            st.stop()
    except:
        pass

def send_log(url, name, action):
    try: requests.post(url, json={"name": name, "action": action}, timeout=5)
    except: pass

# --- 2. STUDENT MODE ---
if "form" in params:
    config = {
        "form": params.get("form"),
        "hook": params.get("hook"),
        "ref": params.get("ref"),
        "tool": params.get("tool")
    }

    if 'has_started' not in st.session_state: st.session_state.has_started = False
    if 'is_active' not in st.session_state: st.session_state.is_active = True

    c1, c2 = st.columns([7, 3])
    with c1: st.title("📝 Online Examination")
    with c2:
        if not st.session_state.has_started:
            with st.form("start"):
                s_name = st.text_input("Student Full Name:", placeholder="Enter your name to begin")
                if st.form_submit_button("🚀 START EXAM", use_container_width=True):
                    if s_name:
                        st.session_state.student_name = s_name
                        st.session_state.has_started = True
                        send_log(config['hook'], s_name, "START")
                        st.rerun()
        else:
            if st.session_state.is_active:
                st.info(f"👤 Candidate: **{st.session_state.student_name}**")
                if st.button("🏁 FINISH & SUBMIT", type="primary", use_container_width=True):
                    send_log(config['hook'], st.session_state.student_name, "FINISH")
                    st.session_state.is_active = False
                    st.toast("Submission recorded. Anti-cheat deactivated.")
            if not st.session_state.is_active:
                st.success("✅ Assessment Completed.")

    st.divider()

    if st.session_state.has_started:
        if st.session_state.is_active:
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

        tab_map = {"✍️ Assignment": config['form']}
        if config['ref'] and config['ref'] != "None": tab_map["📋 Resources"] = config['ref']
        if config['tool'] and config['tool'] != "None": tab_map["🔍 Tools"] = config['tool']

        tabs = st.tabs(list(tab_map.keys()))
        for i, (name, url) in enumerate(tab_map.items()):
            with tabs[i]:
                st.markdown(f'<iframe src="{url}" width="100%" height="850px" style="border:none;"></iframe>', unsafe_allow_html=True)

# --- 3. TEACHER MODE ---
else:
    st.title("🛠️ Exam Management Console")
    t_setup, t_gen = st.tabs(["📖 Setup Guide", "🚀 Generate Exam Link"])
    
    with t_setup:
        st.markdown("""
        ### 1. Sheet Setup
        - Open a Google Sheet > **Extensions** > **Apps Script**.
        - Paste the `Code.gs` and Save.
        ### 2. Deployment
        - **Deploy** > **New Deployment** > **Web App**.
        - Set access to **Anyone**. Copy the **Web App URL**.
        ### 3. Activation
        - After a student starts, use the **🚀 EXAM TOOLS** menu in your Sheet to initialize the Dashboard.
        """)
            
    with t_gen:
        with st.form("generator"):
            h = st.text_input("Webhook URL (from Apps Script):")
            f = st.text_input("Google Form Link:")
            r = st.text_input("Resource Link (Optional):")
            t = st.text_input("Tool Link (Optional):")
            
            st.write("---")
            st.subheader("⚙️ Expiration Settings (Optional)")
            col1, col2 = st.columns(2)
            with col1:
                exp_date = st.date_input("Lock Date:", value=datetime.date.today())
            with col2:
                exp_time = st.time_input("Lock Time (HH:mm):", value=None)
            
            if st.form_submit_button("GENERATE PORTAL LINK", use_container_width=True):
                if h and f:
                    if exp_time:
                        u_param = f"{exp_date.strftime('%Y%m%d')}{exp_time.strftime('%H%M')}"
                    else:
                        u_param = "None"
                    
                    base_url = "https://online-exam.streamlit.app/" # Update to your URL
                    link = f"{base_url}?form={f}&hook={h}&until={u_param}&ref={r or 'None'}&tool={t or 'None'}"
                    st.success("Link Generated!")
                    st.code(link)
                else:
                    st.error("Webhook and Form links are mandatory.")
