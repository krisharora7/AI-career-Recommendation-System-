# career_ui_app_with_auth_voice.py
import streamlit as st
import pdfplumber
import requests
from chatbot_module import ask_bot
from datetime import datetime
import json
import urllib.parse
import streamlit.components.v1 as components

st.set_page_config(page_title="CareerMind.AI", layout="centered", page_icon="🧠")

# ----------------- Groq Config (same as before) -----------------
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"

# ----------------- Basic Credentials (change as needed) -----------------
# NOTE: replace with proper auth for production. This is minimal local auth.
CREDENTIALS = {
    "krish": "pass123",   # existing default (kept for compatibility)
}

# ----------------- Session state initialization -----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "saved_answers" not in st.session_state:
    st.session_state.saved_answers = []  # list of dicts
if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = None
# Keep user registry in session so new signups are possible
if "users" not in st.session_state:
    st.session_state.users = CREDENTIALS.copy()

# ----------------- Helper: Save answer to session history -----------------
def save_answer(mode: str, user_input: str, output_text: str):
    entry = {
        "mode": mode,
        "input": user_input,
        "output": output_text,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    st.session_state.saved_answers.append(entry)
    st.session_state.last_prediction = entry
    return entry

# ----------------- Career Suggestion via Groq (unchanged) -----------------
def get_career_suggestions_from_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a career recommendation engine. Suggest the top 3 careers based on the user's profile."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 300
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    else:
        return f"⚠️ Error: {response.status_code} - {response.text}"

# ----------------- Extract Resume Text (unchanged) -----------------
def extract_resume_text(uploaded_file):
    if uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    elif uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8").strip()
    else:
        return None

# ----------------- Styling (minimalist, improved contrast) -----------------

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f9fafb, #eef3f9);
        font-family: 'Inter', sans-serif;
        animation: fadeIn 0.9s ease-in-out;
    }
    h1, h2, h3, h4, h5, h6 { color: #111827 !important; font-weight: 700; }
    p, label, .stMarkdown { color: #111827 !important; }
    .stTextInput > div > input, .stTextArea > div > textarea { background-color: #fff !important; color: #111827 !important; border: 1px solid #e6e9ee !important; border-radius: 8px !important; padding: 0.6rem !important; }
    .stFileUploader > div, .stTextArea > div { border-radius: 12px; box-shadow: 0 4px 8px rgba(15,23,42,0.04); background-color: #fff !important; }
    .stTabs [data-baseweb="tab"] { color: #374151 !important; font-weight: 600 !important; background-color: #f3f4f6; border-radius: 8px 8px 0 0; padding: 10px 18px; margin-right: 6px; }
    .stTabs [aria-selected="true"] { background-color: #fff !important; color: #2563eb !important; font-weight: 800; box-shadow: 0 -3px 0 0 #2563eb inset; }
    .stButton > button { background: linear-gradient(135deg,#2563eb,#1e40af); color: white; border-radius: 8px; padding: 0.55rem 1rem; font-weight: 600; transition: all 0.2s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 14px rgba(37,99,235,0.18); }
    @keyframes fadeIn { from {opacity:0} to {opacity:1} }
    @media (max-width: 768px) { .stTabs [data-baseweb="tab"]{ padding:8px 12px; font-size:0.95rem; } }
    </style>
""", unsafe_allow_html=True)

# Add Inter font
st.markdown("""<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">""", unsafe_allow_html=True)

# ----------------- LOGIN PAGE (updated to allow create account) -----------------
def show_login():
    st.title("Welcome to CareerMind.AI")
    st.subheader("Please sign in to continue")
    with st.form("login_form", clear_on_submit=False):
        action = st.radio("Action", ["Sign In", "Create Account"], index=0, horizontal=True)
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        submitted = st.form_submit_button("🔐 Sign in" if action == "Sign In" else "🆕 Create account")
    if submitted:
        if action == "Create Account":
            # simple signup stored in session users (in-memory)
            if not username or not password:
                st.error("Please provide username and password to create an account.")
            elif username in st.session_state.users:
                st.error("Username already exists. Please sign in or choose another name.")
            else:
                st.session_state.users[username] = password
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Account created and signed in.")
                st.rerun()
        else:
            # Sign In
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials. (You can create a new account using Create Account.)")

def show_logout():
    if st.sidebar.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# If not logged in -> show login page
if not st.session_state.logged_in:
    show_login()
    st.stop()

# ----------------- App header -----------------
show_logout()  # logout button in sidebar
st.markdown("""
    <div style="text-align:center; margin-bottom:10px;">
        <h1 style="margin-bottom:6px;">🧠 CareerMind.AI</h1>
        <div style="color:#6b7280;">Your personalized career guide</div>
        <div style="font-size:0.85rem; margin-top:6px; color:#9ca3af;">Logged in as: <strong>{}</strong></div>
    </div>
""".format(st.session_state.username), unsafe_allow_html=True)

# Ensure button text contrast is always high
st.markdown("""
<style>
.stButton > button, .stDownloadButton > button {
    color: white !important;
    font-weight: 600 !important;
    background-color: #2563eb !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background-color: #1e40af !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- Saved answers viewer in sidebar ----------
with st.sidebar.expander("💾 Saved Answers", expanded=False):
    if st.session_state.saved_answers:
        for i, e in enumerate(reversed(st.session_state.saved_answers), 1):
            st.markdown(f"**{i}. [{e['mode']}] {e['timestamp']}**")
            st.write(e['output'] if len(e['output']) < 250 else e['output'][:240] + "...")
            cols = st.columns([1,1,1])
            with cols[0]:
                # download each as txt
                txt = f"Mode: {e['mode']}\nTime: {e['timestamp']}\n\nINPUT:\n{e['input']}\n\nOUTPUT:\n{e['output']}"
                st.download_button(f"⬇️ Download", txt, file_name=f"career_{i}.txt", key=f"dl_{i}")
            with cols[1]:
                # share via mailto - use JS open for reliability
                subject = urllib.parse.quote(f"Career suggestion from CareerMind ({e['mode']})")
                body = urllib.parse.quote(txt)
                mailto = f"mailto:?subject={subject}&body={body}"
                share_html = f'''
                    <a href="{mailto}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;">
                        <button style="padding:6px 10px; border-radius:8px; border:1px solid #e5e7eb; background:#fff; cursor:pointer;">
                            ✉️ Share via Email
                        </button>
                    </a>
                    '''


                components.html(share_html, height=45)
            with cols[2]:
                # Copy to clipboard using components (works more reliably)
                safe_text_js = e['output'].replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\n", "\\n").replace('"','\\"')
                copy_html = f"""
                <button id="copy_sidebar_{i}" style="padding:6px 10px; border-radius:6px; border:1px solid #e5e7eb; background:#2563eb; color:#fff; cursor:pointer;">
                    📋 Copy
                </button>
                <script>
                document.getElementById("copy_sidebar_{i}").onclick = async () => {{
                    const text = `{safe_text_js}`;
                    try {{
                        await navigator.clipboard.writeText(text);
                        alert('Copied to clipboard!');
                    }} catch (err) {{
                        // fallback
                        const ta = document.createElement('textarea');
                        ta.value = text;
                        document.body.appendChild(ta);
                        ta.select();
                        document.execCommand('copy');
                        document.body.removeChild(ta);
                        alert('Copied to clipboard (fallback).');
                    }}
                }};
                </script>
                """
                components.html(copy_html, height=60)

        # download all as json
        st.markdown("---")
        combined = json.dumps(list(reversed(st.session_state.saved_answers)), indent=2)
        st.download_button("⬇️ Download All (JSON)", combined, file_name="career_saved_all.json")
    else:
        st.write("No saved answers yet. Your generated suggestions will appear here.")

# ----------------- Query param based voice-transcript handling -----------------
# If the browser was redirected with ?transcript=..., pick it up and clear params
params = st.query_params
prefilled_transcript = params.get("transcript", "")
if prefilled_transcript:
    st.session_state["_voice_transcript"] = urllib.parse.unquote(prefilled_transcript)
    st.query_params.clear()

st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: #1f2937; /* dark gray */
}
[data-testid="stSidebar"] * {
    color: #f9fafb !important; /* light text */
}
</style>
""", unsafe_allow_html=True)

# Ensure all text inside alerts and markdown is readable
st.markdown("""
<style>
.stMarkdown, .stAlert p, .stAlert span {
    color: #111827 !important; /* dark text */
}
</style>
""", unsafe_allow_html=True)

# ----------------- Tabs: Resume / Manual / Chat -----------------
tab1, tab2, tab3 = st.tabs(["📄 Resume-Based", "📝 Manual Entry", "🤖 Chat Assistant"])

# ----------------- 1) Resume tab -----------------
with tab1:
    st.header("📄 Resume-Based Prediction")
    st.markdown("Upload your resume (PDF or TXT) for personalized career suggestions.")
    uploaded_resume = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"], key="resume_uploader")

    if uploaded_resume:
        resume_text = extract_resume_text(uploaded_resume)
        if resume_text:
            st.text_area("📃 Resume Preview", resume_text[:2000], height=260, key="resume_preview")
            if st.button("🔍 Analyze Resume & Predict Careers", key="resume_predict"):
                with st.spinner("🧠 Analyzing your resume..."):
                    prompt = f"""
Here is a student's resume:

{resume_text}

Based on their skills, education, and experience, suggest the top 3 most suitable career paths. 
For each career, provide:
1. Career title
2. Brief reason why it's a good fit (1 sentence)
3. Growth potential (High/Medium/Low)

Format as a numbered list with bold titles.
"""
                    prediction = get_career_suggestions_from_groq(prompt)
                st.success("🎯 Suggested Career Paths:")
                st.markdown(prediction)
                # save to history
                save_answer("Resume", resume_text[:2000], prediction)
        else:
            st.warning("❌ Unable to extract text from resume. Please try another file.")

# ----------------- 2) Manual Entry tab -----------------
with tab2:
    st.header("📝 Manual Entry Prediction")
    st.markdown("Fill your details to receive career suggestions tailored to your profile.")
    col1, col2 = st.columns(2)
    with col1:
        skills = st.text_input("Skills (comma-separated)", placeholder="e.g., Python, Data Analysis, Communication", key="skills_input")
        interests = st.text_input("Interests (comma-separated)", placeholder="e.g., Technology, Healthcare", key="interests_input")
        degree = st.selectbox("Degree", ["", "High School", "Bachelor's", "Master's", "PhD", "Other"], key="degree_select")
    with col2:
        cgpa = st.text_input("CGPA (if applicable)", placeholder="e.g., 3.5", key="cgpa_input")
        experience = st.text_input("Years of Experience", placeholder="e.g., 2", key="experience_input")
        age = st.text_input("Age (optional)", placeholder="e.g., 24", key="age_input")

    if st.button("🎯 Get Career Recommendations", key="manual_predict"):
        if skills and interests and degree:
            with st.spinner("🔍 Finding career matches..."):
                prompt = f"""
A student has entered the following information:
- Skills: {skills}
- Interests: {interests}
- Degree: {degree}
- CGPA: {cgpa if cgpa else 'Not specified'}
- Experience: {experience if experience else 'None'} years
- Age: {age if age else 'Not specified'}

Suggest 3 most suitable career paths. For each career, provide:
1. Career title (bold)
2. Brief reason why it's a good fit (1 sentence)
3. Required skills to improve (if any)

Format as a numbered list.
"""
                prediction = get_career_suggestions_from_groq(prompt)
            st.success("✨ Recommended Career Paths:")
            st.markdown(prediction)
            save_answer("Manual", prompt, prediction)
        else:
            st.error("Please fill Skills, Interests, and Degree fields at minimum.")

# ----------------- 3) Chat Assistant tab (with voice options) -----------------
with tab3:
    st.header("🤖 Career Assistant")
    st.markdown("Ask any career-related questions and get personalized advice. Use voice input (🎤) or play assistant answer (🔊).")

    # Prefill with voice transcript if exists
    default_chat = st.session_state.pop("_voice_transcript", "") if "_voice_transcript" in st.session_state else ""
    user_question = st.text_area("Your career question", value=default_chat, height=140, key="chat_input")

    # microphone button via components (redirects parent after recognition)
    mic_html = """
        <div style="display:flex; gap:10px; align-items:center; margin-bottom:8px;">
            <button id="start-rec" style="padding:8px 12px; border-radius:8px; border:none; background:#2563eb; color:white; font-weight:bold; cursor:pointer;">🎤 Speak (fill question)</button>
            <small style="color:#6b7280; margin-left:8px;">(Requires Chrome/Edge on HTTPS or localhost)</small>
        </div>
        <script>
        const btn = document.getElementById('start-rec');
        btn.onclick = () => {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert('Speech recognition not supported. Try Chrome or Edge.');
                return;
            }
            const recog = new SpeechRecognition();
            recog.lang = 'en-US';
            recog.interimResults = false;
            recog.maxAlternatives = 1;
            recog.onresult = (event) => {
                const text = event.results[0][0].transcript;
                // Instead of redirect, directly set text in textarea
                const ta = window.parent.document.querySelector('textarea[aria-label="Your career question"]');
                if (ta) {
                    ta.value = text;
                    ta.dispatchEvent(new Event('input', { bubbles: true }));
                }
            };
            recog.onerror = (e) => { alert('Speech recognition error: ' + e.error); };
            recog.start();
        };
        </script>
        """


    components.html(mic_html, height=90)

    # Chat submit button
    if st.button("💬 Ask CareerMind", key="chat_ask"):
        if user_question.strip():
            answer = ask_bot(user_question.strip())
            st.success("💡 CareerMind's Response:")
            st.markdown(answer)

            # ✅ Escape ` and newlines in Python before inserting into JS
            safe_answer = answer.replace("`", "\\`").replace("\n", " \\n ")

            js_play = f"""
            <button id="play_ans" style="padding:8px 12px; border-radius:8px; border:none; background:#2563eb; color:white; font-weight:bold; cursor:pointer;">🔊 Play Answer</button>
            <script>
            document.getElementById('play_ans').onclick = () => {{
                const text = `{safe_answer}`;
                const ut = new SpeechSynthesisUtterance(text);
                ut.lang = 'en-US';
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(ut);
            }};
            </script>
            """
            components.html(js_play, height=60)

            # Save to history
            save_answer("Chat", user_question.strip(), answer)
        else:
            st.warning("Please enter a question.")

# ----------------- Optional: show last prediction and quick actions -----------------
if st.session_state.last_prediction:
    e = st.session_state.last_prediction
    with st.expander("📝 Last generated suggestion (quick actions)"):
        st.markdown(f"**Mode:** {e['mode']} • **Time:** {e['timestamp']}")
        st.markdown("**Output:**")
        st.write(e['output'])
        cols = st.columns([1,1,1])
        with cols[0]:
            txt = f"Mode: {e['mode']}\nTime: {e['timestamp']}\n\nINPUT:\n{e['input']}\n\nOUTPUT:\n{e['output']}"
            st.download_button("⬇️ Download", txt, file_name="last_career.txt")
        with cols[1]:
            subject = urllib.parse.quote(f"Career suggestion from CareerMind ({e['mode']})")
            body = urllib.parse.quote(txt)
            mailto = f"mailto:?subject={subject}&body={body}"
            # use JS open for reliable behavior
            share_html = f'''
            <a href="{mailto}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;">
                <button style="padding:6px 10px; border-radius:8px; border:1px solid #e5e7eb; background:#fff; cursor:pointer;">
                    ✉️ Share via Email
                </button>
            </a>
            '''


            components.html(share_html, height=45)
        with cols[2]:
            safe_text_js = e['output'].replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\n", "\\n").replace('"','\\"')
            copy_html = f"""
            <button id="copy_last" style="padding:6px 10px; border-radius:6px; border:1px solid #e5e7eb; background:#2563eb; color:#fff; cursor:pointer;">
                📋 Copy output
            </button>
            <script>
            document.getElementById('copy_last').onclick = async () => {{
                const text = `{safe_text_js}`;
                try {{
                    await navigator.clipboard.writeText(text);
                    alert('Copied to clipboard!');
                }} catch (err) {{
                    const ta = document.createElement('textarea');
                    ta.value = text;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    alert('Copied to clipboard (fallback).');
                }}
            }};
            </script>
            """
            components.html(copy_html, height=60)

# ----------------- Footer / tips -----------------
st.markdown("---")
st.markdown("Tip: For voice input use Chrome/Edge desktop. For persistent account-backed history, integrate a user DB (recommended for production).")


