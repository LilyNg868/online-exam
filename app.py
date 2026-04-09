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
# 3  STUDENT MODE: 
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

# --- 4. TEACHER GENERATOR MODE ---
else:
    st.markdown('<h1 class="main-title">🛠️ Assignment Engine</h1>', unsafe_allow_html=True)
    l, r = st.columns(2, gap="large")
   
    with l:
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
