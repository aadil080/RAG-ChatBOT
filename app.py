import streamlit as st
import requests
from dotenv import load_dotenv
from voice import generating_audio

# Loading environment variables from .env file
load_dotenv()

# Title of the app
st.title("Sarvam AI Assessment", anchor=False)

# CSS for custom styling (increasing font size of assistant's text)
css_for_text = """
<style>
    .text {
        font-size: 24px;
    }
</style>
"""
# Applying the custom CSS for styling
st.markdown(css_for_text, unsafe_allow_html=True)

# Chat input field where the user can type their prompt
prompt = st.chat_input("Say something")

# Process the input only if the user has entered something
if prompt:

    # Initializing User and Assistant chat messages
    user = st.chat_message("user")
    assistant = st.chat_message("assistant")

    # Display the user's prompt in the chat with custom CSS styling
    user.markdown(f"<p class='text'>{prompt}</p>", unsafe_allow_html=True)
    try:
        # Send the user's prompt to the backend API for generating a response
        response = requests.get(f"http://localhost:8080/to_agent/{prompt}").json()

        # Check if the API returned a valid response and whether it's a string (text-based)
        if isinstance(response.get('output', ''), str):
            # Extract the response text, clean it up, and display it in the chat
            output_text = response.get('output', '').replace('\"', '').replace('\\n', '').strip()
            
            # Generate audio from the assistant's response text
            audio_buffer = generating_audio(output_text)

            # Display the assistant's response in the chat with formatting
            assistant.markdown(f"<p class='text'>{output_text}</p>", unsafe_allow_html=True)

            # Play the generated audio directly on the Streamlit app
            st.audio(audio_buffer, format="audio/wav")

        else:
            # If the response is not a string, handle it as a list of related articles
            output_list = response.get('output', '')

            # Display a message that the query is unrelated to the topic
            assistant.markdown(f"<p class='text'>The query is not related to sound.<br/>"
                            "So, I would recommend you to go through these articles for more information:</p>", 
                            unsafe_allow_html=True)

            # Iterate through the output list and display each article with its title and URL
            for title, link in output_list:

                # Clean up the link by removing any trailing commas
                link = link.replace(',', '')

                # Display each article's title and a clickable URL
                assistant.markdown(f"<hr/><p class='text'>Title: {title} <br/>"
                                f"URL: <a href={link}>{link}</a></p>", 
                                unsafe_allow_html=True)
    except Exception as e:
        # Display an error message if the API request fails
        assistant.markdown(f"<p class='text'>Sorry, I couldn't process your request.<br/> There is some problem I am facing right now. Please try again later.</p>", 
                            unsafe_allow_html=True)
        # print(e)
