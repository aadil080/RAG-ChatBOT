import streamlit as st
import requests
from dotenv import load_dotenv
from voice import generating_audio

load_dotenv()

# Set title of the app
st.title("Sarvam AI Assessment", anchor=False)

# Define CSS for styling
css_for_text = """
<style>
    .assistant_text {
        font-size: 24px;
    }
</style>
"""
st.markdown(css_for_text, unsafe_allow_html=True)

# Chat input
prompt = st.chat_input("Say something")

# Process the input
if prompt:
    user = st.chat_message("user")
    assistant = st.chat_message("assistant")
    # Make a GET request to the API
    user.markdown(f"<p class='assistant_text'>{prompt}</p>", unsafe_allow_html=True)
    response = requests.get(f"http://localhost:8080/to_agent/{prompt}")
    data = response.json()

    # Get output from response and format it
    output_text = data.get('output', '').replace('\"', '').replace('\\n', '').strip()
    # print("output_text: ", output_text)
    # Generate audio from the output text
    audio_buffer = generating_audio(output_text)

    # Display the formatted output
    assistant.markdown(f"<p class='assistant_text'>{output_text}</p>", unsafe_allow_html=True)

    st.audio(audio_buffer, format="audio/wav")
