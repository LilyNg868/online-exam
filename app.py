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
                    st.toast("Submission logged. Monitoring deactivated.")
            
            if not st.session_state.is_active:
                st.success("✅ Exam is finished. You may now view your result.")

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


# --- 3. TEACHER MODE ---
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
 */
function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var logSheet = ss.getSheetByName("Logs") || ss.getSheets()[0];
  if (logSheet.getName() !== "Logs") logSheet.setName("Logs");

  var data = JSON.parse(e.postData.contents);
  logSheet.appendRow([new Date(), data.name, data.action]);
  return ContentService.createTextOutput("Success");
}

/**
 * 2. CUSTOM MENU
 */
function onOpen() {
  SpreadsheetApp.getUi().createMenu('🚀 EXAM TOOLS')
      .addItem('Setup Live Dashboard', 'setupDashboard')
      .addToUi();
}

/**
 * 3. DASHBOARD GENERATOR
 */
function setupDashboard() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var logSheet = ss.getSheetByName("Logs");
  var sep = ";"; 
  
  if (!logSheet) {
    SpreadsheetApp.getUi().alert("Logs tab not found!");
    return;
  }

  var dashSheet = ss.getSheetByName("LIVE_MONITOR") || ss.insertSheet("LIVE_MONITOR");
  dashSheet.clear().activate();

  // --- STATISTICS ---
  dashSheet.getRange("A1:B1").merge().setValue("📊 STATISTICS").setBackground("#1f4e78").setFontColor("white").setFontWeight("bold").setHorizontalAlignment("center");
  dashSheet.getRange("A3").setValue("Total Students Started:");
  dashSheet.getRange("B3").setFormula(`=IFERROR(COUNTUNIQUE(FILTER(Logs!B:B${sep} UPPER(TRIM(Logs!C:C))="START"))${sep} 0)`);
  dashSheet.getRange("A4").setValue("Completed:");
  dashSheet.getRange("B4").setFormula(`=COUNTIF(Logs!C:C${sep} "*FINISH*")`);
  dashSheet.getRange("A5").setValue("Total Violations:");
  dashSheet.getRange("B5").setFormula(`=COUNTIF(Logs!C:C${sep} "*LEAVE TAB*")`).setFontColor("red").setFontWeight("bold");

  // --- MONITORING TABLE ---
  dashSheet.getRange("D1:G1").merge().setValue("🚨 STUDENT MONITORING").setBackground("#333333").setFontColor("white").setFontWeight("bold").setHorizontalAlignment("center");
  
  var headers = [["Student Name", "Violations", "Last Violation At", "Status"]];
  dashSheet.getRange("D2:G2").setValues(headers).setBackground("#eeeeee").setFontWeight("bold");

  var nameQuery = `=IFERROR(UNIQUE(QUERY(Logs!A:C${sep} "SELECT B WHERE UPPER(C) CONTAINS 'START'"${sep} 1))${sep} "Waiting...")`;
  dashSheet.getRange("D3").setFormula(nameQuery);

  var lastRow = 200; 

  dashSheet.getRange("E3:E" + lastRow).setFormula(
    `=IF(OR(D3=""${sep} D3="Waiting...")${sep} ""${sep} COUNTIFS(Logs!B:B${sep} D3${sep} Logs!C:C${sep} "*LEAVE TAB*"))`
  );

  dashSheet.getRange("F3:F" + lastRow).setFormula(
    `=IF(OR(D3=""${sep} E3=0)${sep} ""${sep} MAXIFS(Logs!A:A${sep} Logs!B:B${sep} D3${sep} Logs!C:C${sep} "*LEAVE TAB*"))`
  );
  dashSheet.getRange("F3:F" + lastRow).setNumberFormat("HH:mm:ss");

  dashSheet.getRange("G3:G" + lastRow).setFormula(
    `=IF(OR(D3=""${sep} D3="Waiting...")${sep} ""${sep} IF(COUNTIFS(Logs!B:B${sep} D3${sep} Logs!C:C${sep} "*FINISH*")>0${sep} "COMPLETED"${sep} "IN PROGRESS"))`
  );

  // --- AUTO HIGHLIGHT COMPLETED ---
  var range = dashSheet.getRange("D3:G" + lastRow);
  var rule = SpreadsheetApp.newConditionalFormatRule()
      .whenFormulaSatisfied(`=$G3="COMPLETED"`)
      .setBackground("#d9ead3")
      .setFontColor("#274e13")
      .setRanges([range])
      .build();
  
  var rules = dashSheet.getConditionalFormatRules();
  rules.push(rule);
  dashSheet.setConditionalFormatRules(rules);

  dashSheet.setColumnWidth(4, 200); dashSheet.setColumnWidth(5, 100); 
  dashSheet.setColumnWidth(6, 150); dashSheet.setColumnWidth(7, 120);

  SpreadsheetApp.getUi().alert("Dashboard is updated.");
}
            """, language="javascript")
       

        
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
