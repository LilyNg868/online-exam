import streamlit as st
import streamlit.components.v1 as components
import requests
import datetime
import pytz

# --- 1. SETTINGS & AUTO-LOCK ---
st.set_page_config(page_title="Exam Portal", layout="wide")
params = st.query_params

# Check Deadline if exists in URL
if "until" in params and params.get("until") != "None":
    try:
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now = datetime.datetime.now(vn_tz)
        deadline_str = params.get("until") # Format: HHmm
        deadline_time = now.replace(hour=int(deadline_str[:2]), minute=int(deadline_str[2:]), second=0)
        
        if now > deadline_time:
            st.error(f"🚫 This exam portal closed at {deadline_time.strftime('%H:%M')}. Access denied.")
            st.stop()
    except: pass

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
                s_name = st.text_input("Candidate Name:", placeholder="Full name")
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
                    st.toast("Monitoring deactivated.")
            if not st.session_state.is_active:
                st.success("✅ Examination Completed.")

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
    
    with t_gen:
        with st.form("generator"):
            h = st.text_input("Webhook URL:")
            f = st.text_input("Google Form Link:")
            
            col_a, col_b = st.columns(2)
            with col_a:
                exp_time = st.time_input("Lock Portal At (Optional):", value=None)
            with col_b:
                r = st.text_input("Resource Link:")
            
            t = st.text_input("Tool Link:")
            
            if st.form_submit_button("CREATE PORTAL LINK"):
                if h and f:
                    # Mã hóa thời gian vào URL (HHmm)
                    until_param = exp_time.strftime("%H%M") if exp_time else "None"
                    base_url = "https://online-exam.streamlit.app/" 
                    link = f"{base_url}?form={f}&hook={h}&until={until_param}&ref={r or 'None'}&tool={t or 'None'}"
                    st.success("Exam Link Generated!")
                    st.code(link)
