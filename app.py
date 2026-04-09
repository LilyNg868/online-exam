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
    .main-title { font-size: 2.8rem; font-weight: 800; color: #1E293B; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

params = st.query_params

# --- 2. TEACHER LIVE DASHBOARD MODE ---
if "view" in params:
    st.markdown('<h1 class="main-title">📊 Live Class Monitor</h1>', unsafe_allow_html=True)
    sheet_link = params.get("view")
    
    try:
        file_id = sheet_link.split("/d/")[1].split("/")[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"
        df = pd.read_csv(csv_url, names=['Timestamp', 'Student', 'Action'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Students Joined", df[df['Action']=='START']['Student'].nunique())
        m2.metric("Completed", df[df['Action']=='FINISH']['Student'].nunique())
        m3.metric("Tab Switches", len(df[df['Action']=='LEAVE TAB']), delta_color="inverse")

        st.divider()
        col_l, col_r = st.columns([6, 4])
        with col_l:
            st.subheader("🚨 Violation Log")
            st.dataframe(df[df['Action']=='LEAVE TAB'].sort_values('Timestamp', ascending=False), use_container_width=True)
        with col_r:
            st.subheader("📈 Completion Progress")
            total_s = df[df['Action']=='START']['Student'].nunique()
            total_f = df[df['Action']=='FINISH']['Student'].nunique()
            fig = px.pie(values=[total_f, max(0, total_s - total_f)], names=['Finished', 'In Progress'], 
                         color_discrete_sequence=['#22C55E', '#EAB308'], hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        if st.button("🔄 Refresh Data", use_container_width=True): st.rerun()
    except:
        st.error("Enable 'Anyone with the link can view' on your Google Sheet.")

# --- 3. STUDENT EXAM MODE ---
elif "form" in params:
    FORM_URL = params.get("form")
    HOOK_URL = params.get("hook")
    REF_URL = params.get("ref") if params.get("ref") != "None" else None
    TOOL_URL = params.get("tool") if params.get("tool") != "None" else None
    
    if 'has_started' not in st.session_state: st.session_state.has_started = False
    if 'active' not in st.session_state: st.session_state.active = True

    c1, c2 = st.columns([7, 3])
    with c1: st.title("📝 Online Assignment")
    with c2:
        if not st.session_state.has_started:
            with st.form("start"):
                name = st.text_input("Full Name:")
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
                st.success("Submitted!")

    if st.session_state.has_started and st.session_state.active:
        components.html(f"""
            <script>
            document.addEventListener("visibilitychange", function() {{
                if (document.hidden) {{
                    fetch('{HOOK_URL}', {{method: 'POST', mode: 'no-cors', body: JSON.stringify({{name: '{st.session_state.student_name}', action: 'LEAVE TAB'}})}});
                    alert("VIOLATION: Tab switching recorded!");
                }}
            }});
            </script>
        """, height=0)
        
        tabs_titles = ["✍️ Assignment"]
        if REF_URL: tabs_titles.append("📋 Reference")
        if TOOL_URL: tabs_titles.append("🔍 Extra Tool")
        
        tabs = st.tabs(tabs_titles)
        with tabs[0]:
            st.markdown(f'<iframe src="{FORM_URL}" width="100%" height="900px" style="border:none;"></iframe>', unsafe_allow_html=True)
        
        idx = 1
        if REF_URL:
            with tabs[idx]:
                st.markdown(f'<iframe src="{REF_URL}" width="100%" height="900px"></iframe>', unsafe_allow_html=True)
            idx += 1
        if TOOL_URL:
            with tabs[idx]:
                st.markdown(f'<iframe src="{TOOL_URL}" width="100%" height="900px"></iframe>', unsafe_allow_html=True)

# --- 4. TEACHER GENERATOR MODE ---
else:
    st.markdown('<h1 class="main-title">🛠️ Assignment Engine</h1>', unsafe_allow_html=True)
    l, r = st.columns(2, gap="large")
    with l:
        st.subheader("Step 1: Database Setup")
        with st.expander("Instructions", expanded=True):
            st.markdown("1. Create a [Sheet](https://sheets.new). 2. Add Apps Script. 3. Deploy as Web App (Anyone). 4. Share Sheet as 'Anyone with link can view'.")
            st.code("function doPost(e){var s=SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();var d=JSON.parse(e.postData.contents);s.appendRow([new Date(),d.name,d.action]);return ContentService.createTextOutput('OK');}", language="javascript")

    with r:
        st.subheader("Step 2: Generate Links")
        with st.form("gen"):
            f_hook = st.text_input("Webhook URL:")
            f_form = st.text_input("Google Form Link:")
            f_sheet = st.text_input("Google Sheet URL (Dashboard):")
            f_ref = st.text_input("Reference/Formula Link (Optional):")
            f_tool = st.text_input("Extra Tool Link (Optional):")
            
            if st.form_submit_button("CREATE PORTAL", use_container_width=True):
                if f_hook and f_form and f_sheet:
                    # Update with your actual Streamlit URL
                    base = "https://online-exam.streamlit.app/" 
                    s_link = f"{base}?form={f_form}&hook={f_hook}&ref={f_ref or 'None'}&tool={f_tool or 'None'}"
                    t_link = f"{base}?view={f_sheet}"
                    st.success("Links Ready!")
                    st.write("**Student Link:**"); st.code(s_link)
                    st.write("**Teacher Dashboard:**"); st.code(t_link)
