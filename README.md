<h1 align="center" id="title">RAG Based Chatbot</h1>

<p id="description">The RAG-based AI ChatBot is designed to streamline information retrieval from lengthy PDF files and web Articles catering to professionals like researchers teachers and engineers. Utilizing Pinecone Vector Database Gemini API and GoogleGenerativeAI it generates relevant answers from internal documents. Built with Streamlit for the frontend and FastAPI for the backend the chatbot leverages Langchain to handle queries efficiently. The project offers fast and accurate insights optimizing document-based research and decision-making processes.</p>
  
<h2>🧐 Features</h2>

Here're some of the project's best features:

*   Easy to use
*   No data is stored
*   Completely made with python

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
docker build -t <image_name> .

```

<p>4. </p>

```
docker build -t <image_name> .

```
  
<h2>💻 Built with</h2>

Technologies used in the project:

*   Python
*   Docker
*   Streamlit
*   Langchain
*   Sarvam AI Text to Speech

<h2>🛡️ License:</h2>

This project is licensed under the Apache-2.0 license
