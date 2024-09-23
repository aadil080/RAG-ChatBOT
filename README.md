<h1 align="center" id="title">RAG Based Chatbot</h1>

<p id="description">The RAG-based AI ChatBot is designed to streamline information retrieval from lengthy PDF files, catering to professionals like Researchers, Teachers, Engineers and anyone. Utilizing **Pinecone Vector Database, Gemini API and Sarvam AI** it generates relevant answers from internal documents. Also, it generates the speech out of the response by llm. Built with Streamlit for the frontend and FastAPI for the backend the chatbot leverages Langchain to handle queries efficiently. The project offers fast and accurate insights optimizing document-based research and decision-making processes.</p>

<p>The primary data of this project is based upon Chapter 11 - Sound, Book Science of CBSE class 9<sup>th</sup>. To change the data for personal use. <br/> Open file named **"api.py"** go to the **line 164** and instead of **"./data/ncert_data.pdf"** paste the filepath of your document. Rerun the script and your program is good to go.</p>
  
<h2>🧐 Features</h2>

Here're some of the project's best features:

*   Completely built with python.
*   Uses less memory and computing power.
*   Can be hosted on local machine.
*   Handle Queries efficiently.

<h2>🛠️ Installation Steps:</h2>

<h3>By basic way</h3>

<p>1. Clone the repo</p>

```
git clone https://github.com/aadil080/Sarvam-ML-Assignment.git
```

<p>2. Change the Working directory and install the requirements</p>

```
pip install -r requirements.txt
```

<p>3. Create & add environment variables in ".env" file</p>

```
PINECONE_API_KEY = <your_pinecone_index_api_key>
PINECONE_INDEX_NAME = <your_pinecone_name>
GOOGLE_API_KEY = <your_google_gemini_1.5_flash_api_key>
SARVAM_API_KEY = <your_sarvam_ai_text_to_speech_api_key>
```

<p>4. Execute the bash file</p>

```
bash start.sh
```

<h3>Using Docker</h3>

<p>1. Clone the repo</p>

```
git clone https://github.com/aadil080/Sarvam-ML-Assignment.git
```

<p>2. Create & add environment variables in ".env" file</p>

```
PINECONE_API_KEY = <your_pinecone_index_api_key>
PINECONE_INDEX_NAME = <your_pinecone_name>
GOOGLE_API_KEY = <your_google_gemini_1.5_flash_api_key>
SARVAM_API_KEY = <your_sarvam_ai_text_to_speech_api_key>
```

<p>3. Execute docker image creation command</p>

```
docker build -t <image_name> . # here period represents the dockerfile path
```

<p>4. Create a new container from the created image</p>

```
docker run -p 8000:80 <image_name>
```

<h2>Usage</h2>
<p>After Installation step, Open browser on same machine and type this below address:</p>

```
http://localhost:8501
```
  
<h2>💻 Built with</h2>

Python is used as a main language to build this project.

Python Libraries mainly used in project:

*   Streamlit
*   Langchain
*   FastAPI

APIs used in the project:

*   Sarvam AI Text to Speech
*   Google Gemini 1.5 Flash
*   Pinecone Vector Database

Version control tool and Contianerization Technologies 
*   Docker
*   Github


<h2>🛡️ License:</h2>

This project is licensed under the Apache-2.0 license
