import streamlit as st
import streamlit.components.v1 as components
import requests

# --- 1. SETTINGS ---
st.set_page_config(page_title="Exam Portal", layout="wide")

# CSS tối giản, tập trung vào trải nghiệm làm bài
st.markdown("""
    <style>
    div[data-testid="InputInstructions"] { display: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f1f5f9; border-radius: 5px; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

params = st.query_params

# Hàm gửi dữ liệu gọn nhẹ
def send_log(url, name, action):
    try:
        requests.post(url, json={"name": name, "action": action}, timeout=5)
    except:
        pass

# --- 2. STUDENT MODE ---
if "form" in params:
    # Lấy params gọn hơn
    config = {
        "form": params.get("form"),
        "hook": params.get("hook"),
        "ref": params.get( "ref" if "ref" in params else "sheet"), # Hỗ trợ cả 2 tên biến
        "tool": params.get("tool")
    }

    if 'has_started' not in st.session_state: st.session_state.has_started = False
    if 'is_active' not in st.session_state: st.session_state.is_active = True

    c1, c2 = st.columns([7, 3])
    with c1: st.title("📝 Online Assessment")
    with c2:
        if not st.session_state.has_started:
            with st.form("start"):
                s_name = st.text_input("Full Name:", placeholder="Enter your name to start")
                if st.form_submit_button("🚀 START EXAM", use_container_width=True):
                    if s_name:
                        st.session_state.student_name = s_name
                        st.session_state.has_started = True
                        send_log(config['hook'], s_name, "START")
                        st.rerun()
                    else: st.error("Name is required.")
        
        elif st.session_state.is_active:
            st.info(f"👤 **{st.session_state.student_name}** | Monitoring Active")
            if st.button("🏁 FINISH EXAM", type="primary", use_container_width=True):
                send_log(config['hook'], st.session_state.student_name, "FINISH")
                st.session_state.is_active = False
                st.rerun()
        else:
            st.success("✅ Examination Completed.")

    st.divider()

    if st.session_state.has_started and st.session_state.is_active:
        # Anti-cheat: Thêm thông báo toast thay vì alert gây treo trang
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

        # Tab Logic tối ưu: Chỉ tạo tab nếu URL tồn tại và không phải "None"
        tab_map = {"✍️ Assignment": config['form']}
        if config['ref'] and config['ref'] != "None": tab_map["📋 Reference"] = config['ref']
        if config['tool'] and config['tool'] != "None": tab_map["🔍 Tools"] = config['tool']

        tabs = st.tabs(list(tab_map.keys()))
        for i, (name, url) in enumerate(tab_map.items()):
            with tabs[i]:
                # Tự động nhận diện ảnh hoặc iframe
                if any(url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                    st.image(url, use_container_width=True)
                else:
                    st.markdown(f'<iframe src="{url}" width="100%" height="850px" style="border:none;"></iframe>', unsafe_allow_html=True)

# --- 3. TEACHER MODE ---
else:
    st.title("🛠️ Teacher Control Panel")
    t_setup, t_gen = st.tabs(["📖 Setup Guide", "🚀 Link Generator"])
    
    with t_setup:
        st.info("Copy the Apps Script code from the expander below and deploy it in Google Sheets.")
        with st.expander("📄 Click to copy Apps Script Code"):
            st.code("/* Code Apps Script của bạn ở đây */", language="javascript")
            
    with t_gen:
        with st.form("generator"):
            h = st.text_input("Webhook URL (from Apps Script):")
            f = st.text_input("Google Form Link:")
            r = st.text_input("Reference/PDF (Optional):")
            t = st.text_input("Tool Link (Optional):")
            if st.form_submit_button("GENERATE EXAM LINK", use_container_width=True):
                if h and f:
                    # Tự động lấy URL hiện tại của App để làm base
                    # (Streamlit tự xử lý URL khi deploy)
                    s_link = f"https://online-exam.streamlit.app/?form={f}&hook={h}&ref={r or 'None'}&tool={t or 'None'}"
                    st.success("Link Generated!")
                    st.code(s_link)
                else:
                    st.error("Please fill in Webhook and Form links.")
