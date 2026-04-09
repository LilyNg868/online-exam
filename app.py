import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Exam Portal", layout="wide")

st.markdown("""
    <style>
    div[data-testid="InputInstructions"] { display: none; }
    .stApp { max-width: 1200px; margin: 0 auto; }
    .main-title { font-size: 2.5rem; font-weight: 800; color: #1E293B; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

params = st.query_params
# 2  STUDENT MODE: 
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
            st.success("✅ Session Completed. You may now view your result.")

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
# --- 3. TEACHER MODE (GENERATOR + INSTRUCTIONS) ---
else:
    st.markdown('<h1 class="main-title">🛠️ Teacher Control Panel</h1>', unsafe_allow_html=True)
    
    tab_setup, tab_gen = st.tabs(["📖 Step-by-Step Setup Guide", "🚀 Generate Exam Link"])

    with tab_setup:
        st.subheader("How to set up your Real-time Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="step-box">
            <strong>1. Prepare Google Sheet</strong><br>
            - Create a new <a href="https://sheets.new" target="_blank">Google Sheet</a>.<br>
            - Go to <b>Extensions > Apps Script</b>.<br>
            - Paste the provided script and <b>Save</b>.
            </div>
            
            <div class="step-box">
            <strong>2. Deploy Web App</strong><br>
            - Click <b>Deploy > New Deployment</b>.<br>
            - Select type: <b>Web App</b>.<br>
            - Access: <b>Anyone</b>.<br>
            - Copy the <b>Web App URL</b> (this is your Webhook).
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="step-box">
            <strong>3. Initialize Dashboard</strong><br>
            - Refresh your Sheet.<br>
            - Go to menu <b>🚀 EXAM TOOLS > Setup Live Dashboard</b>.<br>
            - Click <b>Share</b> and set to <b>'Anyone with the link can view'</b>.
            </div>
            
            <div class="step-box">
            <strong>4. Generate Student Link</strong><br>
            - Go to the next tab here (🚀 Generate Exam Link).<br>
            - Paste your URLs and get the link for students.
            </div>
            """, unsafe_allow_html=True)

        with st.expander("📄 Copy Apps Script Code"):
            st.code("""
// Paste this in Google Apps Script
function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var logSheet = ss.getSheetByName("Logs") || ss.getSheets()[0];
  if (logSheet.getName() !== "Logs") logSheet.setName("Logs");
  var data = JSON.parse(e.postData.contents);
  logSheet.appendRow([new Date(), data.name, data.action]);
  return ContentService.createTextOutput("Success");
}

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🚀 EXAM TOOLS').addItem('Setup Live Dashboard', 'setupDashboard').addToUi();
}

function setupDashboard() {
  // (Paste the full setupDashboard function code here from the previous message)
}
            """, language="javascript")

    with tab_gen:
        st.subheader("Generate Monitored Exam Link")
        with st.form("generator_form"):
            f_hook = st.text_input("1. Webhook URL (from Apps Script):", placeholder="https://script.google.com/macros/s/.../exec")
            f_form = st.text_input("2. Google Form Link:", placeholder="https://docs.google.com/forms/d/...")
            f_ref = st.text_input("3. Reference Link (Optional):", placeholder="e.g., PDF Formula Sheet")
            f_tool = st.text_input("4. Extra Tool Link (Optional):", placeholder="e.g., Online Calculator")
            
            if st.form_submit_button("CREATE STUDENT PORTAL", use_container_width=True):
                if f_hook and f_form:
                    # Tự động lấy URL hiện tại của app
                    base_url = "https://online-exam.streamlit.app/" # Thay bằng URL thật của bạn
                    
                    s_link = f"{base_url}?form={f_form}&hook={f_hook}&ref={f_ref or 'None'}&tool={f_tool or 'None'}"
                    
                    st.success("🎉 Exam Link Generated!")
                    st.write("**Send this to your students:**")
                    st.code(s_link)
                    st.info("Remember: Watch your live updates in the Google Sheet 'LIVE_MONITOR' tab.")
                else:
                    st.error("Please provide at least Webhook URL and Google Form Link.")

