import streamlit as st
import requests
# from dotenv import load_dotenv
from voice import generating_audio

def wide_space_default():
    st.set_page_config(layout="wide")

wide_space_default()

st.header("Sarvam AI Assessment", anchor=False)

# CSS for custom styling (increasing font size of assistant's text)
css_for_text = """
<style>
    p, li, strong, ul {
        font-size: 22px;
    }

    h1 {
        font-size: 28px;
    }
</style>
"""

@st.cache_data
def uploading_web_url():
    clearing_cache()
    print("url", url)

@st.cache_data
def uploading_file(uploaded_file):
    print("uploaded_file name", uploaded_file.name)
    files_bytes = uploaded_file.read()
    print("files_bytes", len(files_bytes))
    
    # print("Pdf Uploading by read_doc()")
    response = requests.post("http://localhost:8000/upload_document", files={"file_bytes": files_bytes, "file_name": uploaded_file.name}).json()
    # st.markdown(response['status'], unsafe_allow_html=True)
    return response

def clearing_cache():
    print("Clearing Cache...")
    uploading_file.clear()
    print("Cleared Cache")

def formatting_answer(answer):
    answer = answer.replace("<h1>", "<h2>").replace("<h1/>", "<h2/>")
    return answer


# Applying the custom CSS for styling
st.markdown(css_for_text, unsafe_allow_html=True)

# Chat input field where the user can type their prompt
prompt = st.chat_input("Say something")

response = {"status":""}

with st.sidebar:
    with st.expander("Upload PDF"):
        uploaded_file = st.file_uploader("Upload PDF", label_visibility='hidden', type="pdf", key="file", accept_multiple_files=False, on_change=clearing_cache)

        if uploaded_file is not None:
            response = uploading_file(uploaded_file)
            # st.write(response['status'])
    with st.expander("Enter Web URL"):
        url = st.text_input(label="Enter URL",placeholder = "https://www.google.com", label_visibility="hidden")
        st.button("Submit", type="primary", on_click=uploading_web_url)

    proffesions = ["Researcher", "Engineer", "Teacher", "Lawyer", "Student", "Doctor", "Other"]
    proffesion = st.selectbox("Select your Proffesion for better results", proffesions)

desc = st.markdown(response['status'], unsafe_allow_html=True)

# Process the input only if the user has entered something
if prompt:
    desc.empty()
    # Initializing User and Assistant chat messages
    user = st.chat_message("user")
    assistant = st.chat_message("assistant")

    # Display the user's prompt in the chat with custom CSS styling
    user.markdown(f"<p class='text'>{prompt}</p>", unsafe_allow_html=True)
    try:
        # Send the user's prompt to the backend API for generating a response
        response = requests.get(f"http://localhost:8080/to_agent", params={"query": prompt, "proffesion": proffesion}).json()

        # Check if the API returned a valid response and whether it's a string (text-based)
        if isinstance(response.get('output', ''), str):
            # Extract the response text, clean it up, and display it in the chat
            output_text = response.get('output', '').replace('\"', '').replace('\\n', '').strip()
            
            # Generate audio from the assistant's response text
            # audio_buffer = generating_audio(output_text)

            # Display the assistant's response in the chat with formatting
            assistant.markdown(f"<p class='text'>{formatting_answer(output_text)}</p>", unsafe_allow_html=True)

            # Play the generated audio directly on the Streamlit app
            # st.audio(audio_buffer, format="audio/wav")

        else:
            # If the response is not a string, handle it as a list of related articles
            output_list = response.get('output', '')

            # Display a message that the query is unrelated to the topic
            assistant.markdown(f"<p class='text'>The query is not related to data you have provided.<br/>"
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
