import streamlit as st
import streamlit.components.v1 as components
import requests

# --- 1. SETTINGS ---
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

# --- 2. STUDENT INTERFACE ---
if "form" in params:
    config = {
        "form": params.get("form"),
        "hook": params.get("hook"),
        "ref": params.get("ref"),
        "tool": params.get("tool")
    }

    # Initialize session states
    if 'has_started' not in st.session_state: st.session_state.has_started = False
    if 'is_active' not in st.session_state: st.session_state.is_active = True

    c1, c2 = st.columns([7, 3])
    with c1: st.title("📝 Online Examination")
    
    with c2:
        # Phase 1: Registration
        if not st.session_state.has_started:
            with st.form("start"):
                s_name = st.text_input("Candidate Name:", placeholder="Enter full name")
                if st.form_submit_button("🚀 START EXAM", use_container_width=True):
                    if s_name:
                        st.session_state.student_name = s_name
                        st.session_state.has_started = True
                        send_log(config['hook'], s_name, "START")
                        st.rerun() # Only rerun here to enter the exam
        
        # Phase 2: Monitoring & Finishing
        else:
            if st.session_state.is_active:
                st.info(f"👤 Candidate: **{st.session_state.student_name}**")
                # We use a standard button instead of a form to avoid forced refreshes
                if st.button("🏁 FINISH", type="primary", use_container_width=True):
                    send_log(config['hook'], st.session_state.student_name, "FINISH")
                    st.session_state.is_active = False
                    # IMPORTANT: No st.rerun() here to keep the iframe state
                    st.toast("Examination is finished. You may now view your result.")
            
            if not st.session_state.is_active:
                st.success("✅ Logged as Finished. You may continue reviewing.")

    st.divider()

    # Phase 3: Persistent Content Layout
    if st.session_state.has_started:
        
        # Anti-cheat JS: Only runs if is_active is True
        # Using a container to hold the JS so it can be "removed" when state changes
        js_placeholder = st.empty()
        if st.session_state.is_active:
            with js_placeholder:
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
        else:
            js_placeholder.empty() # Remove the JS monitoring entirely

        # Tab Layout: This remains untouched during the "Finish" process
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
            /**
 * 1. CORE DATA RECEIVER
 * Automatically initializes the "Logs" sheet upon the first student action.
 */
function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var logSheet = ss.getSheetByName("Logs");

  // Auto-rename the first sheet to "Logs" if it doesn't exist
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
  var sep = ";"; // Hardcoded for your region to prevent #ERROR!
  
  // Identify or create the Logs sheet
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
    SpreadsheetApp.getUi().alert("No data received yet. Please start an exam to initialize the Logs sheet.");
    return;
  }

  var dashSheet = ss.getSheetByName("LIVE_MONITOR") || ss.insertSheet("LIVE_MONITOR");
  dashSheet.clear().activate();

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
  // Fixed Syntax: Using backticks to handle single quotes within the QUERY
  var queryStr = `=QUERY(Logs!A:C${sep} "SELECT B, COUNT(C), MAX(A) WHERE C = 'LEAVE TAB' GROUP BY B ORDER BY COUNT(C) DESC LABEL B 'Student Name', COUNT(C) 'Times', MAX(A) 'Latest Violation'"${sep} 1)`;
  dashSheet.getRange("D2").setFormula(queryStr);

  // PROGRESS PIE CHART
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

  // Formatting
  dashSheet.getRange("F:F").setNumberFormat("HH:mm:ss");
  dashSheet.setColumnWidth(4, 180); dashSheet.setColumnWidth(5, 70); dashSheet.setColumnWidth(6, 130);
  dashSheet.hideColumns(13, 2); 
  
  SpreadsheetApp.getUi().alert("Dashboard updated successfully!");
}
            """, language="javascript")
            
    with t_gen:
        with st.form("generator"):
            h = st.text_input("Webhook URL (from Apps Script Deployment):")
            f = st.text_input("Google Form Link:")
            r = st.text_input("Resource Link (Optional):")
            t = st.text_input("Tool Link (Optional):")
            if st.form_submit_button("GENERATE PORTAL LINK", use_container_width=True):
                if h and f:
                    base_url = "https://online-exam.streamlit.app/" 
                    final_link = f"{base_url}?form={f}&hook={h}&ref={r or 'None'}&tool={t or 'None'}"
                    st.success("Exam Link Generated!")
                    st.code(final_link)
                else: st.error("Webhook and Form links are mandatory.")
