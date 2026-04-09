import streamlit as st
import streamlit.components.v1 as components
import requests
import urllib.parse
import pandas as pd
import plotly.express as px

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Exam Management System", layout="wide")

st.markdown("""
    <style>
    div[data-testid="InputInstructions"] { display: none; }
    .stApp { max-width: 1200px; margin: 0 auto; }
    .main-title { font-size: 2.8rem; font-weight: 800; color: #1E293B; }
    .card { background-color: #F8FAFC; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; }
    </style>
    """, unsafe_allow_html=True)

params = st.query_params

# --- 2. TEACHER LIVE DASHBOARD MODE ---
if "view" in params:
    st.markdown('<h1 class="main-title">📊 Live Class Monitor</h1>', unsafe_allow_html=True)
    sheet_link = params.get("view")
    
    try:
        # Transform Sheet URL to CSV Export URL
        file_id = sheet_link.split("/d/")[1].split("/")[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"
        
        # Load Data
        df = pd.read_csv(csv_url, names=['Timestamp', 'Student', 'Action'])
        
        # Statistics
        total_started = df[df['Action']=='START']['Student'].nunique()
        total_finished = df[df['Action']=='FINISH']['Student'].nunique()
        total_violations = len(df[df['Action']=='LEAVE TAB'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Students Joined", total_started)
        m2.metric("Completed", total_finished)
        m3.metric("Total Tab Switches", total_violations, delta_color="inverse")

        st.divider()
        col_left, col_right = st.columns([6, 4])

        with col_left:
            st.subheader("🚨 Real-time Violation Log")
            violations = df[df['Action']=='LEAVE TAB'].sort_values('Timestamp', ascending=False)
            st.dataframe(violations, use_container_width=True, height=400)

        with col_right:
            st.subheader("📈 Completion Progress")
            progress_data = pd.DataFrame({
                "Status": ["Finished", "In Progress"],
                "Count": [total_finished, total_started - total_finished]
            })
            fig = px.pie(progress_data, values='Count', names='Status', 
                         color_discrete_sequence=['#22C55E', '#EAB308'], hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    except Exception:
        st.error("Error: Could not read data. Ensure your Google Sheet is shared as 'Anyone with the link can view'.")

# --- 3. STUDENT EXAM MODE ---
elif "form" in params:
    FORM_URL = params.get("form")
    HOOK_URL = params.get("hook")
    
    if 'has_started' not in st.session_state: st.session_state.has_started = False
    if 'active' not in st.session_state: st.session_state.active = True

    c1, c2 = st.columns([7, 3])
    with c1: st.title("✍️ Online Assignment")
    with c2:
        if not st.session_state.has_started:
            with st.form("student_start"):
                name = st.text_input("Full Name:", placeholder="Enter your name")
                if st.form_submit_button("🚀 START"):
                    if name:
                        st.session_state.student_name = name
                        st.session_state.has_started = True
                        requests.post(HOOK_URL, json={"name": name, "action": "START"})
                        st.rerun()
        else:
            st.write(f"Student: **{st.session_state.student_name}**")
            if st.button("🏁 FINISH EXAM", type="primary"):
                requests.post(HOOK_URL, json={"name": st.session_state.student_name, "action": "FINISH"})
                st.session_state.active = False
                st.success("Submitted successfully!")

    if st.session_state.has_started and st.session_state.active:
        components.html(f"""
            <script>
            document.addEventListener("visibilitychange", function() {{
                if (document.hidden) {{
                    fetch('{HOOK_URL}', {{method: 'POST', mode: 'no-cors', body: JSON.stringify({{name: '{st.session_state.student_name}', action: 'LEAVE TAB'}})}});
                    alert("VIOLATION: Tab switching is recorded!");
                }}
            }});
            </script>
        """, height=0)
        st.markdown(f'<iframe src="{FORM_URL}" width="100%" height="900px" style="border:none;"></iframe>', unsafe_allow_html=True)

# --- 4. TEACHER GENERATOR MODE (Landing Page) ---
else:
    st.markdown('<h1 class="main-title">🛠️ Exam Engine Setup</h1>', unsafe_allow_html=True)
    st.write("Generate custom exams and live dashboards instantly.")

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Step 1: Database Setup")
        with st.expander("Instructions", expanded=True):
            st.markdown("""
            1. Open [Google Sheets](https://sheets.new).
            2. **Extensions > Apps Script**, paste the code, and **Deploy as Web App** (Set access to 'Anyone').
            3. **IMPORTANT:** Click **Share** on your Sheet and set to **'Anyone with the link can view'**.
            """)
            st.code("""function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var data = JSON.parse(e.postData.contents);
  sheet.appendRow([new Date(), data.name, data.action]);
  return ContentService.createTextOutput("Success");
}""", language="javascript")

    with right:
        st.subheader("Step 2: Generate Portal")
        with st.form("generator"):
            f_hook = st.text_input("Webhook URL (from Apps Script):")
            f_form = st.text_input("Google Form Link:")
            f_sheet = st.text_input("Google Sheet URL (the spreadsheet itself):")
            
            if st.form_submit_button("CREATE EXAM & DASHBOARD", use_container_width=True):
                if f_hook and f_form and f_sheet:
                    # Update this to your actual Streamlit URL
                    base = "https://online-exam-8vextpoluxbfd75ea5kdnb.streamlit.app/" 
                    s_link = f"{base}?form={f_form}&hook={f_hook}"
                    t_link = f"{base}?view={f_sheet}"
                    
                    st.success("Links Generated Successfully!")
                    st.write("📂 **Send to Students:**")
                    st.code(s_link)
                    st.write("📈 **Teacher Dashboard (Keep private):**")
                    st.code(t_link)
                else:
                    st.error("Please fill in all 3 links.")
