import streamlit as st
import streamlit.components.v1 as components
import requests

st.set_page_config(page_title="Exam Portal", layout="wide")

st.markdown("""
    <style>
    div[data-testid="InputInstructions"] { display: none; }
    .stApp { max-width: 1200px; margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)

params = st.query_params

def send_log(url, name, action):
    try: requests.post(url, json={"name": name, "action": action}, timeout=5)
    except: pass

# --- STUDENT INTERFACE ---
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
                s_name = st.text_input("Candidate Name:", placeholder="Enter full name")
                if st.form_submit_button("🚀 START EXAM", use_container_width=True):
                    if s_name:
                        st.session_state.student_name = s_name
                        st.session_state.has_started = True
                        send_log(config['hook'], s_name, "START")
                        st.rerun()
        elif st.session_state.is_active:
            st.info(f"👤 Candidate: **{st.session_state.student_name}**")
            if st.button("🏁 FINISH & SUBMIT", type="primary", use_container_width=True):
                send_log(config['hook'], st.session_state.student_name, "FINISH")
                st.session_state.is_active = False
                st.rerun()
        else: st.success("✅ Examination Completed.")

    st.divider()

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

        tab_map = {"✍️ Assignment": config['form']}
        if config['ref'] and config['ref'] != "None": tab_map["📋 Resources"] = config['ref']
        if config['tool'] and config['tool'] != "None": tab_map["🔍 Tools"] = config['tool']

        tabs = st.tabs(list(tab_map.keys()))
        for i, (name, url) in enumerate(tab_map.items()):
            with tabs[i]:
                st.markdown(f'<iframe src="{url}" width="100%" height="850px" style="border:none;"></iframe>', unsafe_allow_html=True)

# --- TEACHER INTERFACE ---
else:
    st.title("🛠️ Exam Management Console")
    t_setup, t_gen = st.tabs(["📖 Setup Guide", "🚀 Generate Exam Link"])
    
    with t_setup:
        st.markdown("""
        ### Phase 1: Google Sheets Setup
        1. Open a new [Google Sheet](https://sheets.new).
        2. Go to **Extensions** > **Apps Script**.
        3. Paste the provided code into `Code.gs`.
        4. Click **Deploy** > **New Deployment**.
        5. Select **Web App**, set access to **Anyone**, and click **Deploy**.
        6. **Copy the Web App URL** for the next step.

        ### Phase 2: Activation
        - Send the generated link to students.
        - Once the first student starts, a menu **🚀 EXAM TOOLS** will appear in your Sheet.
        - Click **Setup Live Dashboard** to initialize the monitor.
        """)
        
        with st.expander("📄 View Apps Script Code"):
            st.code("""
            /* Use the Javascript code provided above in the Apps Script section */
            """, language="javascript")
            
    with t_gen:
        with st.form("generator"):
            h = st.text_input("Webhook URL (from Apps Script Deployment):")
            f = st.text_input("Google Form Link:")
            r = st.text_input("Resource Link (Optional):")
            t = st.text_input("Tool Link (Optional):")
            if st.form_submit_button("GENERATE PORTAL LINK", use_container_width=True):
                if h and f:
                    base_url = "https://your-app-name.streamlit.app/" 
                    final_link = f"{base_url}?form={f}&hook={h}&ref={r or 'None'}&tool={t or 'None'}"
                    st.success("Exam Link Generated!")
                    st.code(final_link)
                else: st.error("Webhook and Form links are mandatory.")
