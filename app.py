import streamlit as st
import base64
import os
from google import genai
from google.genai import types
from streamlit_local_storage import LocalStorage
import json 

st.set_page_config(
    page_title="Telugu Audio to English Text Converter",
    page_icon=":microphone:",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
        font-family: "Segoe UI", sans-serif;
    }
 
    .stDownloadButton > button {
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5em 1em;
    }
    hr {
        border-top: 1px solid #bbb;
    }
    </style>
""", unsafe_allow_html=True)

st.header("🎙️ Telugu Audio to English Text Converter")
st.markdown("Convert **Telugu audio** into **English text** using AI")
st.markdown("<hr>", unsafe_allow_html=True)

if os.path.exists("config.json"):
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
else:
    config = {
        "model_name": "gemini-2.0-flash",
        "temperature": 0.2,
        "max_output_tokens": 512,
        "response_mime_type": "text/plain",
        "MAX_FILE_SIZE_MB": 25
    }

localS = LocalStorage()

if "to_go" not in st.session_state:
    st.session_state.to_go = False

if "genai_api_key" not in st.session_state:
    st.session_state.genai_api_key = None

if "voice_clip_data" not in st.session_state:
    st.session_state.voice_clip_data = None

if 'clicked' not in st.session_state:
    st.session_state.clicked = False

def click_button():
    st.session_state.clicked = True
    
def get_api_key():

    streamlit_genai_key = st.text_input(
        label="Enter your GenAI API Key",
        type="password",
        key="genai_api_key_input",
        help="Enter your GenAI API Key to use the service."
    )

    if st.button("Submit API Key", on_click=click_button)):
        if st.session_state.clicked:
            st.session_state.genai_api_key = streamlit_genai_key
            localS.setItem("genai_api_key", streamlit_genai_key)
            
try:
    stored_key = localS.getItem("genai_api_key")
    if stored_key and stored_key.get("value"):
        stored_key = stored_key["value"]
except:
    stored_key = None

if st.session_state.genai_api_key:
    st.session_state.to_go = True
elif stored_key:
    st.session_state.genai_api_key = stored_key
    st.session_state.to_go = True
else:
    st.warning("Please enter your GenAI API Key to use the service.")
    get_api_key()
    st.session_state.to_go = False

if os.path.exists("prompt.txt"):
    with open("prompt.txt", "r") as file:
        prompt = file.read()
else:
    prompt = "Please transcribe this Telugu audio to English text."

def get_base64_audio(uploaded_file):
    st.session_state.voice_clip_data = base64.b64encode(uploaded_file.read()).decode('utf-8')
    return st.session_state.voice_clip_data

def generate(base64_data, client):
    model = config.get("model_name", "gemini-2.0-flash")
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
                types.Part.from_bytes(
                    mime_type="audio/x-m4a",
                    data=base64.b64decode(base64_data),
                ),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=config.get("temperature", 0.2),
        max_output_tokens=config.get("max_output_tokens", 512),
        response_mime_type=config.get("response_mime_type", "text/plain")
    )
    data_out = client.models.generate_content(
        model=model, contents=contents, config=generate_content_config
    )
    return data_out

data_out = None

if st.session_state.to_go:
    with st.container():
        st.subheader("📤 Step 1: Upload Telugu Audio File")
        col1, col2 = st.columns([2, 3])
        with col1:
            streamlit_audio = st.audio_input(
                label="Upload Audio (M4A format)",
                key="audio_input",
                help="Only M4A format is supported currently."
            )
            
            if streamlit_audio:
                st.success("Audio uploaded! Ready to transcribe.")

    MAX_FILE_SIZE_MB = config.get("MAX_FILE_SIZE_MB", 25)
    if streamlit_audio is not None:
        file_size_mb = len(streamlit_audio.read()) / (1024 * 1024)
        streamlit_audio.seek(0) 
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error("File too large. Please upload a file smaller than 25 MB.")
        else:
            base64_data = get_base64_audio(streamlit_audio)        

        if base64_data:
            try:
                client = genai.Client(api_key=st.session_state.genai_api_key)
                with st.spinner("🔄 Transcribing... Please wait."):
                    data_out = generate(st.session_state.voice_clip_data, client)
            except Exception as e:
                st.error(f"❌ Error during transcription: {str(e)}")
                data_out = None

    if data_out:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("📝 Step 2: Transcribed English Text")
        st.code(data_out.text)

        st.download_button(
            label="⬇️ Download Transcription",
            data=data_out.text,
            file_name="output.txt",
            mime="text/plain"
        )
    elif streamlit_audio and st.session_state.voice_clip_data:
        st.error("❌ Failed to generate content. Please check the audio and try again.")

st.markdown("<hr>", unsafe_allow_html=True)
if st.button("🔁 Reset App"):
    st.session_state.to_go = False
    st.session_state.genai_api_key = None
    st.session_state.voice_clip_data = None
    try:
        localS.deleteItem("genai_api_key")
    except:
        pass
    st.rerun()
