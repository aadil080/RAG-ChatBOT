import requests
import streamlit as st
import base64
import io
import os
from dotenv import load_dotenv

def generating_audio(text):
    load_dotenv()
    url = "https://api.sarvam.ai/text-to-speech"

    payload = {
        "inputs": [text],
        "target_language_code": "hi-IN",
        "speaker": "meera",
        "pitch": 0,
        "pace": 1.00,
        "loudness": 1.5,
        "speech_sample_rate": 16000,
        "enable_preprocessing": True,
        "model": "bulbul:v1"
    }

    headers = {
        "Content-Type": "application/json",
        "API-Subscription-Key": os.environ['SARVAM_API_KEY']
    }

    response = requests.request("POST", url, json=payload, headers=headers).json()
    audio_raw = ''

    for audio in response['audios']:
        audio_raw += audio

    # print(os.environ['SARVAM_API_KEY'])

    decoded_audio = base64.b64decode(audio_raw)

    # Create an in-memory file-like object for the WAV data
    audio_buffer = io.BytesIO(decoded_audio)

    # Display the audio using Streamlit's audio component
    # st.audio(audio_buffer, format="audio/wav")

    return audio_buffer

    # print("response.text: " , response['audios'])