import streamlit as st
import streamlit.components.v1 as components
import requests
import urllib.parse

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Exam Portal Engine", layout="wide")

# CUSTOM CSS: Professional UI and hiding technical instructions
st.markdown("""
    <style>
    div[data-testid="InputInstructions"] { display: none; }
    .stApp { max-width: 1200px; margin: 0 auto; }
    .main-title { color: #0e1117; font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem; }
    .instruction-box { background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #007bff; }
    /* Primary button styling */
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MODE DETECTION LOGIC ---
params = st.query_params

# STUDENT MODE: Triggered if 'form' exists in the URL
if "form" in params:
    FORM_URL = params.get("form")
    HOOK_URL = params.get("hook")
    SHEET_URL = params.get("sheet") if params.get("sheet") != "None" else None
    TOOL_URL = params.get("tool") if params.get("tool") != "None" else None

    if 'is_monitored' not in st.session_state: st.session_state.is_monitored = True
    if 'has_started' not in st.session_state: st.session_state.has_started = False

    col_l, col_r = st.columns([7, 3])
    with col_l:
        st.title("📝 Online Assessment")
    with col_r:
        if not st.session_state.has_started:
            with st.form("start_exam"):
                st.write("Enter your full name to begin:")
                s_name = st.text_input("Student Name:", placeholder="e.g. Jane Doe")
                # Enter key will automatically trigger this button
                if st.form_submit_button("🚀 START EXAM", use_container_width=True):
                    if s_name:
                        st.session_state.student_name = s_name
                        st.session_state.has_started = True
                        try: requests.post(HOOK_URL, json={"name": s_name, "action": "START"})
                        except: pass
                        st.rerun()
                    else: st.error("Name is required to start.")
        elif st.session_state.is_monitored:
            if st.button("🏁 CONFIRM FINISH", type="primary", use_container_width=True):
                try: requests.post(HOOK_URL, json={"name": st.session_state.student_name, "action": "FINISH"})
                except: pass
                st.session_state.is_monitored = False
                st.rerun()
            st.caption(f"Student: **{st.session_state.student_name}** | 🔒 Monitoring Active")
        else:
            st.success("✅ Session Completed. You may close this tab.")

    st.divider()

    if st.session_state.has_started:
        # JavaScript Monitoring (Anti-cheat)
        status_js = "true" if st.session_state.is_monitored else "false"
        components.html(f"""
            <script>
            var active = {status_js};
            document.addEventListener("visibilitychange", function() {{
                if (active && document.hidden) {{
                    fetch('{HOOK_URL}', {{
                        method: 'POST', mode: 'no-cors',
                        body: JSON.stringify({{ name: '{st.session_state.get('student_name', '')}', action: 'LEAVE TAB' }})
                    }});
                    alert("WARNING: You left the exam tab! This incident has been reported to the teacher.");
                }}
            }});
            </script>
        """, height=0)

        # Content Tabs
        t_names = ["✍️ Assignment"]
        if SHEET_URL: t_names.append("📋 Formula Sheet")
        if TOOL_URL: t_names.append("🔍 Tools")
        
        tabs = st.tabs(t_names)
        with tabs[0]:
            st.markdown(f'<iframe src="{FORM_URL}" width="100%" height="900px" style="border:none;"></iframe>', unsafe_allow_html=True)
        
        idx = 1
        if SHEET_URL:
            with tabs[idx]:
                if any(SHEET_URL.lower().endswith(e) for e in ['.png', '.jpg', '.jpeg']):
                    st.image(SHEET_URL, use_container_width=True)
                else:
                    st.markdown(f'<iframe src="{SHEET_URL}" width="100%" height="900px"></iframe>', unsafe_allow_html=True)
            idx += 1
        if TOOL_URL:
            with tabs[idx]:
                st.markdown(f'<iframe src="{TOOL_URL}" width="100%" height="900px"></iframe>', unsafe_allow_html=True)

# TEACHER MODE: Default landing page for link generation
else:
    st.markdown('<h1 class="main-title">🛠️ Exam Portal Generator</h1>', unsafe_allow_html=True)
    st.write("Deploy secure, monitored exams in minutes. No GitHub or coding knowledge required for teachers.")
    
    c1, c2 = st.columns([1, 1], gap="large")
    
    with c1:
        st.subheader("📖 Step 1: Setup Your Database")
        with st.container(border=True):
            st.markdown("""
            **1. Create a Sheet:** Open a new **[Google Sheet](https://sheets.new)** and give it a name (e.g., 'Exam Logs').

            **2. Open Script Editor:** Go to **Extensions** > **Apps Script**.

            **3. Paste the Code:** Delete all existing code in the editor and paste this:
            """)
            st.code("""function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var data = JSON.parse(e.postData.contents);
  sheet.appendRow([new Date(), data.name, data.action]);
  return ContentService.createTextOutput("Success");
}""", language="javascript")
            
            st.markdown("""
            **4. Deploy as Web App:** * Click **Deploy** (blue button) > **New Deployment**.
            * Select Type: **Web App**.
            * Description: `v1`
            * Execute as: **Me** (your email).
            * Who has access: **Anyone** (This is critical).
            * Click **Deploy**.

            **5. Authorize Access:** * A popup will ask for permission. Click **Authorize Access**.
            * Select your Google Account.
            * If you see *"Google hasn't verified this app"*, click **Advanced** > **Go to [Project Name] (unsafe)**.
            * Click **Allow**.

            **6. Copy URL:** Copy the **Web App URL** (ends in `/exec`) and paste it into Step 2 on the right.
            """)

    with c2:
        st.subheader("🔗 Step 2: Generate Exam Link")
        with st.form("teacher_form"):
            t_hook = st.text_input("Web App URL (from Step 1):", placeholder="https://script.google.com/...")
            t_form = st.text_input("Exam Link:", placeholder="https://docs.google.com/forms/...")
            t_sheet = st.text_input("Formula Sheet (Optional):", placeholder="Link to image/PDF/GitHub")
            t_tool = st.text_input("Extra Tool (Optional):", placeholder="e.g. Desmos calculator link")
            
            if st.form_submit_button("GENERATE STUDENT LINK", use_container_width=True):
                if t_hook and t_form:
                    # IMPORTANT: Update this URL after deploying to Streamlit Cloud
                    base_url = "https://online-exam-8vextpoluxbfd75ea5kdnb.streamlit.app/" 
                    p = {"hook": t_hook, "form": t_form, "sheet": t_sheet or "None", "tool": t_tool or "None"}
                    final_link = f"{base_url}?{urllib.parse.urlencode(p)}"
                    st.success("Success! Send the link below to your students:")
                    st.code(final_link)
                else:
                    st.error("Missing required links (Webhook or Google Form).")
