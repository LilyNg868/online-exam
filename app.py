import streamlit as st
import streamlit.components.v1 as components
import requests

st.set_page_config(page_title="Exam Portal", layout="wide")

# Custom Styles
st.markdown("""
    <style>
    div[data-testid="InputInstructions"] { display: none; }
    .stApp { max-width: 1200px; margin: 0 auto; }
    .setup-card { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 10px; }
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
                s_name = st.text_input("Candidate Name:", placeholder="Enter your full name")
                if st.form_submit_button("🚀 START EXAM", use_container_width=True):
                    if s_name:
                        st.session_state.student_name = s_name
                        st.session_state.has_started = True
                        send_log(config['hook'], s_name, "START")
                        st.rerun()
        elif st.session_state.is_active:
            st.info(f"👤 Candidate: **{st.session_state.student_name}** | 🔒 Secure Mode Active")
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
    t_setup, t_gen = st.tabs(["📖 Detailed Setup Guide", "🚀 Generate Exam Link"])
    
    with t_setup:
        st.markdown("""
        ### Phase 1: Google Sheets Configuration
        1. **Create Sheet**: Open a new [Google Sheet](https://sheets.new).
        2. **Open Script Editor**: Go to **Extensions** > **Apps Script**.
        3. **Paste Code**: Delete all existing code in `Code.gs` and paste the script provided below.
        4. **Save**: Click the 💾 icon and name the project (e.g., "Exam Monitor").

        ### Phase 2: Deployment (Crucial)
        1. Click **Deploy** > **New Deployment**.
        2. Select type: **Web App**.
        3. Set 'Execute as' to **Me**.
        4. Set 'Who has access' to **Anyone**.
        5. Click **Deploy**, authorize permissions, and **copy the Web App URL** (the Webhook).

        ### Phase 3: Activating the Dashboard
        1. Refresh your Google Sheet.
        2. A new menu **🚀 EXAM TOOLS** will appear on the top bar.
        3. Select **Setup Live Dashboard**. 
        *Note: Run this after the first student starts to see real data.*
        """)
        with st.expander("📄 Copy Apps Script Source Code"):
            st.code("/
 * 1. CORE DATA RECEIVER
 * Automatically initializes the "Logs" sheet upon the first student action.
 */
function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var logSheet = ss.getSheetByName("Logs");

  if (!logSheet) {
    logSheet = ss.getSheets()[0]; 
    logSheet.setName("Logs");
  }

  var data = JSON.parse(e.postData.contents);
  logSheet.appendRow([new Date(), data.name, data.action]);
  return ContentService.createTextOutput("Success");
}

/**
 * 2. CUSTOM MENU
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🚀 EXAM TOOLS')
      .addItem('Setup Live Dashboard', 'setupDashboard')
      .addToUi();
}

/**
 * 3. DASHBOARD GENERATOR
 */
function setupDashboard() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sep = ";"; 
  
  var logSheet = ss.getSheetByName("Logs");
  if (!logSheet) {
    var allSheets = ss.getSheets();
    for (var i = 0; i < allSheets.length; i++) {
      if (allSheets[i].getName() !== "LIVE_MONITOR") {
        logSheet = allSheets[i];
        logSheet.setName("Logs");
        break;
      }
    }
  }

  if (!logSheet || logSheet.getLastRow() < 1) {
    SpreadsheetApp.getUi().alert("No data found. Please ensure at least one student has started the exam.");
    return;
  }

  var dashSheet = ss.getSheetByName("LIVE_MONITOR") || ss.insertSheet("LIVE_MONITOR");
  dashSheet.clear();
  dashSheet.activate();

  // HEADERS & STATS
  dashSheet.getRange("A1:B1").merge().setValue("📊 STATISTICS").setBackground("#1f4e78").setFontColor("white").setFontWeight("bold").setHorizontalAlignment("center");
  dashSheet.getRange("A3").setValue("Total Students:");
  dashSheet.getRange("B3").setFormula(`=COUNTIF(Logs!C:C${sep}"START")`);
  dashSheet.getRange("A4").setValue("Completed:");
  dashSheet.getRange("B4").setFormula(`=COUNTIF(Logs!C:C${sep}"FINISH")`);
  dashSheet.getRange("A5").setValue("Total Violations:");
  dashSheet.getRange("B5").setFormula(`=COUNTIF(Logs!C:C${sep}"LEAVE TAB")`).setFontColor("red").setFontWeight("bold");

  // VIOLATION TABLE
  dashSheet.getRange("D1:F1").merge().setValue("🚨 VIOLATION SUMMARY").setBackground("#990000").setFontColor("white").setFontWeight("bold").setHorizontalAlignment("center");
  var queryStr = `=QUERY(Logs!A:C${sep} "SELECT B, COUNT(C), MAX(A) WHERE C = 'LEAVE TAB' GROUP BY B ORDER BY COUNT(C) DESC LABEL B 'Student Name', COUNT(C) 'Times', MAX(A) 'Latest Violation'"${sep} 1)`;
  dashSheet.getRange("D2").setFormula(queryStr);

  // PROGRESS CHART
  dashSheet.getRange("M1").setValue("Status"); dashSheet.getRange("N1").setValue("Count");
  dashSheet.getRange("M2").setValue("Finished"); dashSheet.getRange("N2").setFormula("=B4");
  dashSheet.getRange("M3").setValue("Working"); dashSheet.getRange("N3").setFormula(`=MAX(0${sep}B3-B4)`);

  var chart = dashSheet.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(dashSheet.getRange("M2:N3"))
    .setPosition(2, 8, 0, 0) 
    .setOption('title', 'Completion Progress')
    .setOption('colors', ['#2ecc71', '#f1c40f'])
    .setOption('pieHole', 0.4)
    .build();
  dashSheet.insertChart(chart);

  dashSheet.getRange("F:F").setNumberFormat("HH:mm:ss");
  dashSheet.setColumnWidth(4, 180); dashSheet.setColumnWidth(5, 70); dashSheet.setColumnWidth(6, 130);
  dashSheet.hideColumns(13, 2); 
  
  SpreadsheetApp.getUi().alert("Dashboard updated successfully!");
}", language="javascript")
            
    with t_gen:
        with st.form("generator"):
            h = st.text_input("1. Web App URL (Webhook):", placeholder="https://script.google.com/macros/s/...")
            f = st.text_input("2. Google Form URL:", placeholder="The 'Send' link from your form")
            r = st.text_input("3. Reference URL (Optional):", placeholder="PDF, Formula Sheet, etc.")
            t = st.text_input("4. Tool URL (Optional):", placeholder="Calculator, Periodic Table, etc.")
            if st.form_submit_button("GENERATE PORTAL LINK", use_container_width=True):
                if h and f:
                    base_url = "https://your-app-name.streamlit.app/" 
                    final_link = f"{base_url}?form={f}&hook={h}&ref={r or 'None'}&tool={t or 'None'}"
                    st.success("Exam Link Generated!")
                    st.code(final_link)
                else: st.error("Webhook and Form URLs are mandatory.")
