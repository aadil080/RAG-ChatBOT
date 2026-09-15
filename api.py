from fastapi import FastAPI, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import shutil
import threading
import time
import requests
import bs4

from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate

# Local, disk-persisted FAISS indexes, one per session, so users don't share data
FAISS_ROOT = "/tmp/faiss_indexes"
os.makedirs(FAISS_ROOT, exist_ok=True)
session_stores = {}
session_last_access = {}
SESSION_TTL_SECONDS = 60 * 60  # sessions expire 1 hour after their last use
SWEEP_INTERVAL_SECONDS = 5 * 60

def _session_index_path(session_id):
    return os.path.join(FAISS_ROOT, session_id)

def _touch_session(session_id):
    session_last_access[session_id] = time.time()

def get_session_store(session_id):
    """Loads a session's FAISS store from memory, then disk, returning None if it doesn't exist yet."""
    if session_id in session_stores:
        _touch_session(session_id)
        return session_stores[session_id]
    index_path = _session_index_path(session_id)
    if os.path.isdir(index_path):
        store = FAISS.load_local(index_path, embedding, allow_dangerous_deserialization=True)
        session_stores[session_id] = store
        _touch_session(session_id)
        return store
    return None

def save_session_store(session_id, store):
    session_stores[session_id] = store
    store.save_local(_session_index_path(session_id))
    _touch_session(session_id)

def _delete_session(session_id):
    session_stores.pop(session_id, None)
    session_last_access.pop(session_id, None)
    shutil.rmtree(_session_index_path(session_id), ignore_errors=True)

def _sweep_expired_sessions():
    """Background loop that deletes session FAISS stores (memory + disk) idle for over SESSION_TTL_SECONDS."""
    while True:
        time.sleep(SWEEP_INTERVAL_SECONDS)
        now = time.time()
        expired = [sid for sid, last_used in session_last_access.items() if now - last_used > SESSION_TTL_SECONDS]
        for sid in expired:
            print("Expiring session : ", sid)
            _delete_session(sid)

def _seed_last_access_from_disk():
    """On startup, treat existing on-disk sessions' folder mtime as their last access time."""
    for sid in os.listdir(FAISS_ROOT):
        index_path = _session_index_path(sid)
        if os.path.isdir(index_path):
            session_last_access[sid] = os.path.getmtime(index_path)

def chunk_document(document, chunk_size=600, chunk_overlap=80):
    """
    Divides the document into smaller, overlapping chunks for better processing efficiency.

    Args:
        document (list): A list of fetched content from document.
        chunk_size (int, optional): The maximum number of words ia a chunk. Default is 300.
        chunk_overlap (int, optional): The number of overlapping words between consecutive chunks. Default is 50.

    Returns:
        list: A list of document chunks, where each chunk is a Documentof content with the specified size and overlap.
    """
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_documents(document)
    return chunks

def chunk_article(document, chunk_size=600, chunk_overlap=80):
    """
    Divides the article text into smaller, overlapping chunks for better processing efficiency.

    Args:
        extracted_text (str): The extracted text content from the article URL.
        chunk_size (int, optional): The maximum number of words in a chunk. Default is 300.
        chunk_overlap (int, optional): The number of overlapping words between consecutive chunks. Default is 50.

    Returns:
        list: A list of article chunks, where each chunk is a Documentof content with the specified size and overlap.
    """
    
    splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 80)

    splitted_docs = splitter.split_documents(document)

    return splitted_docs

def uploading_document_to_pinecone(directory, session_id):
    """
    Uploads a document from a specified directory to the session's local FAISS index after processing and chunking the content.

    Args:
        directory (str): The file path of the PDF document that will be indexed.
        session_id (str): The id of the session this document belongs to, keeps users isolated.

    Returns:
        str: A short description of the uploaded document.
    """
    print("Loading PDF : ", directory)
    pdf_loader = PyPDFLoader(directory)
    document = pdf_loader.load()

    # Replacing newline characters with spaces
    for chunk in document:
        chunk.page_content = chunk.page_content.replace('\n', ' ')
    
    # Dividing document content into chunks
    chunked_data = chunk_document(document)

    print("Building local FAISS index for session : ", session_id)
    store = FAISS.from_documents(chunked_data, embedding)
    save_session_store(session_id, store)
    print("Document indexed locally")

    prompt = "What is the Title of the document and a small description of the content."
    description = response_generator(query = prompt, profession="Student", session_id=session_id)
    return description

def uploading_article_to_pinecone(url, session_id):
    strainer = bs4.SoupStrainer(["article", "main"])

    loader = WebBaseLoader(
        web_path = url,
        bs_kwargs = {"parse_only": strainer},
    )

    document = loader.load()
    document[0].page_content = document[0].page_content.replace("\n\n\n", " ").strip()
    document[0].page_content = document[0].page_content.replace("\n\n", " ").strip()

    chunked_data = chunk_article(document)

    print("Building local FAISS index for session : ", session_id)
    store = FAISS.from_documents(chunked_data, embedding)
    save_session_store(session_id, store)
    print("Article indexed locally")

    prompt = "What is the Title of the document and a small description of the content."
    description = response_generator(query = prompt, profession="Student", session_id=session_id)
    return description

def retrieve_response_from_pinecone(query, session_id, k=5):
    """
    Retrieves the most similar chunks from the session's local FAISS index based on the given query.

    Args:
        query (str): The input query used to search the FAISS index for vectors.
        session_id (str): The id of the session whose index should be searched.
        k (int, optional): Indicates top results to choose. Default is 5.

    Returns:
        list: A list of results containing the most similar vectors from the FAISS index.
    """
    
    store = get_session_store(session_id)
    if store is None:
        return []
    results = store.similarity_search(query, k=k)
    return results

def response_generator(query, profession, session_id):
    """
    Generates a response to the given query by retrieving relevant information from the session's local FAISS index and invoking 
    a processing chain with llm.

    Args:
        query (str): The user's input or question that will be used to retrieve relevant information and generate a response.
        session_id (str): The id of the session whose index should be searched.

    Returns:
        str: The generated response to the query, either based on the retrieved information or an error messageif the process fails.
    """
    
    try:
        results = retrieve_response_from_pinecone(query, session_id)
        print("results", results)

        # Generating a response by invoking the chain with retrieved content and the original query
        answer = chain.invoke(input={"profession": profession, "context": results, "user_query": query})
    except Exception as e:
        # Returning an error message if any exception occurs
        answer = f"Sorry, I am unable to find the answer to your query. Please try again later. The error is {e}"
    
    return answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get_response")
def root(query: str, profession: str, session_id: str):
    """
    FastAPI endpoint to handle GET requests and return a generated response for a user's query.

    Args:
        query (str): The query string input from the user, passed as a path parameter in the API request.
        session_id (str): The id of the session whose document index should be searched.

    Returns:
        dict: A dictionary containing the response generated from the query.
    """
    
    print("User_query : " + query)
    answer = response_generator(query, profession, session_id)
    return JSONResponse(content={"answer": answer})

@app.post("/upload_document")
def upload_document(session_id: str, file_bytes: bytes = File(...)):
    """
    FastAPI endpoint to handle POST requests for uploading a document to the session's local FAISS index.

    Args:
        session_id (str): The id of the session this document belongs to.
        file_bytes (bytes): The byte data of the document file that will be indexed.

    Returns:
        dict: A dictionary containing the description of the document uploaded.
    """
    
    try:

        # Save the uploaded file under a session-scoped path so concurrent uploads don't collide
        document_path = f"/tmp/{session_id}_document.pdf"
        with open(document_path, "wb") as f:
            f.write(file_bytes)

        description = uploading_document_to_pinecone(document_path, session_id)
        response = requests.post("http://0.0.0.0:8080/send_desc", json={"description": description, "session_id": session_id})
        return {"status": description}
    except Exception as e:
        return {"status": f"Error uploading file: {e}"}

@app.post("/upload_article")
def upload_article(url: str, session_id: str):
    """
    FastAPI endpoint to handle POST requests for uploading a web article to the session's local FAISS index.

    Args:
        url (string): The string value that contains the url of the web article.
        session_id (str): The id of the session this article belongs to.

    Returns:
        dict: A dictionary containing the description of the article uploaded."""

    try:
        print("URL to server : ", url)

        #Uploading process of article and getting description
        description = uploading_article_to_pinecone(url, session_id)

        # Providing the description to the AI agents
        response = requests.post("http://0.0.0.0:8080/send_desc", json={"description": description, "session_id": session_id})
        print("type(description) : ", type(description))

        # Returning the description of the article
        return {"status": description}
    except Exception as e:
        return {"status": f"Error uploading file: {e}"}

if __name__ == "__main__":
    """
    Initializes the FastAPI server, loads environment variables, creates an embedding model,
    and sets up a language model for generating responses.

    This block of code performs the following tasks:
    - Loads environment variables.
    - Initializes the embedding model used to build/query each session's local FAISS index.
    - Sets up a language model (LLM) for generating human-like responses.
    - Defines the system prompt and response behavior for the assistant.
    - Sets up a chain that combines document retrieval with response generation.
    - Starts the FastAPI server on host `0.0.0.0` at port 8000.
    """

    # Loading environment variables from .env file
    load_dotenv()

    # Initializing embedding model for creating document vectors
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # Expire idle session indexes after 1 hour
    _seed_last_access_from_disk()
    threading.Thread(target=_sweep_expired_sessions, daemon=True).start()

    # Initializing the LLM with the 'gemini-1.5-flash' model and a specified temperature for response generation
    llm = GoogleGenerativeAI(model="gemini-1.5-flash-8b", temperature=0.6)

    # Creating a prompt template for generating responses based on retrieved content and human input
    prompt_template = PromptTemplate(
        template="I am {profession}. I want you to provide a good information regarding my query. You will get additional information from my pdf file: {context}. Here is my query for you: {user_query}. Also use '\\' for newline",
        input_variables=["profession","context", "user_query"]
    )

    # Setting up the document processing chain for response generation based on retrieved documents
    chain = create_stuff_documents_chain(llm, prompt_template, document_variable_name="context")

    # Starting the FastAPI server with Uvicorn, accessible at 0.0.0.0 on port 8000
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
