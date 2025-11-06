# frontend/streamlit_app.py
"""
Streamlit frontend with:
- Left panel: chat history
- Main window: message stream & typing effect
- File upload for PDF/JSON
- Download buttons for DXF + reports
- Dark theme with neon blue accent, FireAI branding
"""

import streamlit as st
import requests
import time
import json
import os

# Backend base URL
BACKEND = "http://127.0.0.1:8000"  # fixed default backend URL
CHAT_URL = f"{BACKEND}/chat"
GENERATE_URL = f"{BACKEND}/generate-dwg"

# Page config & branding
st.set_page_config(page_title="FireAI — Defence RAG Agent", layout="wide", initial_sidebar_state="expanded")

# Inject simple dark theme CSS and logo styling
st.markdown(
    """
    <style>
    .stApp { background-color: #071226; color: #cfefff; }
    .left-panel { background:#041427; padding:12px; border-right:1px solid #0f2a44; height:100vh; }
    .brand { display:flex; align-items:center; gap:12px; }
    .brand img { width:48px; height:48px; border-radius:8px; }
    .neon { color:#0ea5e9; } /* neon blue accent */
    .msg-user { background:#0ea5e9; color:#001; padding:10px; border-radius:8px; margin:6px; align-self:flex-end; max-width:70%;}
    .msg-assistant { background:#0b1b2b; color:#cfefff; padding:10px; border-radius:8px; margin:6px; max-width:70%;}
    .messages { display:flex; flex-direction:column; padding:12px; height:60vh; overflow:auto; }
    .composer { display:flex; gap:8px; align-items:flex-end; }
    textarea { background:#081225; color:#e6eef8; }
    .small { font-size:12px; color:#9fb4c9; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar (left panel) - chat history and file upload
with st.sidebar:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    st.markdown('<div class="brand"><img src="https://via.placeholder.com/48/0ea5e9/001?text=F" alt="logo"/><div><h3 class="neon">FireAI</h3><div class="small">Defence RAG Agent</div></div></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.header("Conversations")
    if "history" not in st.session_state:
        st.session_state.history = []  # list of {"title":..., "messages":[...]}
    # show simple history list
    for i, conv in enumerate(st.session_state.history[::-1]):
        st.write(f"{len(st.session_state.history)-i}. {conv.get('title','Untitled')}")
    st.markdown("---")
    st.header("Upload")
    uploaded_file = st.file_uploader("Upload JSON (layout) or PDF (standards)", type=["json","pdf"])
    if uploaded_file:
        st.write("File uploaded:", uploaded_file.name)
        # Save temporarily
        tmpdir = os.path.join(os.getcwd(), "uploaded_files")
        os.makedirs(tmpdir, exist_ok=True)
        tmp_path = os.path.join(tmpdir, uploaded_file.name)
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("Saved for sending to backend when generating DWG.")

    st.markdown('</div>', unsafe_allow_html=True)

# Main content: chat + composer
st.markdown("<div style='display:flex; gap:16px;'>", unsafe_allow_html=True)
col1, col2 = st.columns([1,3])

with col1:
    st.markdown("### Chat history")
    if "conversation" not in st.session_state:
        st.session_state.conversation = {"title": "New session", "messages": []}
    # show simple list of messages
    for m in st.session_state.conversation["messages"]:
        role = m["role"]
        if role == "user":
            st.markdown(f"<div class='msg-user'>{m['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='msg-assistant'>{m['text']}</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<h2 class='neon'>FireAI — Design Assistant</h2>", unsafe_allow_html=True)
    st.markdown("Describe your layout (e.g., 'Design a 6m x 4m meeting room with 4 sprinklers').", unsafe_allow_html=True)
    prompt = st.text_area("Your prompt", height=120, key="prompt_input")

    # Typing area for streaming assistant reply
    reply_placeholder = st.empty()

    col_button1, col_button2 = st.columns([1,1])
    with col_button1:
        if st.button("Send & Chat (stream)"):
            if not prompt:
                st.warning("Please enter a prompt.")
            else:
                # Append user message to session history
                st.session_state.conversation["messages"].append({"role":"user","text":prompt})
                # call backend streaming /chat
                try:
                    with st.spinner("Getting response..."):
                        # stream response from backend and display typing effect
                        resp = requests.post(CHAT_URL, data={"prompt": prompt}, stream=True, timeout=300)
                        # create visible assistant message gradually
                        assistant_text = ""
                        reply_box = reply_placeholder.empty()
                        for chunk in resp.iter_lines(decode_unicode=True):
                            if not chunk:
                                continue
                            # chunk is raw text from backend streaming (we encoded small pieces)
                            piece = chunk.decode("utf-8") if isinstance(chunk, bytes) else str(chunk)
                            assistant_text += piece
                            # display with typing simulation
                            reply_box.markdown(f"<div class='msg-assistant'>{assistant_text}</div>", unsafe_allow_html=True)
                            time.sleep(0.02)  # small visual typing effect
                        # finalize
                        st.session_state.conversation["messages"].append({"role":"assistant","text":assistant_text})
                except Exception as e:
                    st.error("Error contacting backend: " + str(e))

    with col_button2:
        if st.button("Generate DWG & Reports"):
            # Option: if user uploaded a JSON layout, send that file; otherwise use prompt to ask model for layout
            with st.spinner("Generating layout, DXF and reports..."):
                files = {}
                data = {}
                if uploaded_file and uploaded_file.type == "application/json":
                    # send the uploaded JSON file directly
                    files["upload"] = (uploaded_file.name, uploaded_file.getvalue(), "application/json")
                else:
                    data["prompt"] = prompt

                try:
                    res = requests.post(GENERATE_URL, data=data, files=files, timeout=300)
                    jr = res.json()
                    if jr.get("status") == "success":
                        st.success("DXF and reports generated!")
                        files_info = jr.get("files", {})
                        # show download buttons
                        dxf_url = BACKEND + files_info.get("dxf", "")
                        tech_url = BACKEND + files_info.get("technical_report", "")
                        fin_url = BACKEND + files_info.get("financial_report", "")

                        st.markdown("**Downloads:**")
                        st.markdown(f"- [Download DXF]({dxf_url})")
                        st.markdown(f"- [Download Technical Report]({tech_url})")
                        st.markdown(f"- [Download Financial Report]({fin_url})")

                        # add assistant summary to conversation
                        st.session_state.conversation["messages"].append({"role":"assistant","text":"DXF + reports generated. Use the download links on the page."})
                    else:
                        st.error("Generation failed: " + str(jr))
                except Exception as e:
                    st.error("Error during generation: " + str(e))

st.markdown("</div>", unsafe_allow_html=True)
