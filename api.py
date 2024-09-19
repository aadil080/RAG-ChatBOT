from fastapi import FastAPI
from dotenv import load_dotenv
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

def chunk_data(document, chunk_size=300, chunk_overlap=50):
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

def creating_pinecone_index(embedding):
    """
    Creates a Pinecone index using the provided embedding model.

    Args:
        embedding (object): The embedding model or function used to generate vector embeddings.

    Returns:
        PineconeVectorStore: An instance of Pinecone index where the vectors can be processed.
    """
    
    index = PineconeVectorStore(embedding=embedding)
    return index

def uploading_document_to_pinecone(directory):
    """
    Uploads a document from a specified directory to the Pinecone index after processing and chunking the content.

    Args:
        directory (str): The file path of the PDF document that will be uploaded to Pinecone.

    Returns:
        None: This function does not return any value.
    """
    
    pdf_loader = PyPDFLoader(directory)
    document = pdf_loader.load()

    # Replacing newline characters with spaces
    for line in document:
        line.page_content = line.page_content.replace('\n', ' ')
    
    # Dividing document content into chunks
    chunked_data = chunk_data(document)

    print("Deleting file")
    try:
        # Deleting all existing data on Pinecone index
        pinecone_index.delete(delete_all=True)
        time.sleep(2)
    except:
        print("Namespace is already empty")
    
    print("Uploading File to Pinecone")
    
    # Uploading the chunked data to Pinecone index
    pinecone_index.from_documents(chunked_data, embedding, index_name=index_name)
    print("Document Uploaded to Pinecone")

def retrieve_response_from_pinecone(query, k=5):
    """
    Retrieves the most similar responses from the Pinecone index based on the given query.

    Args:
        query (str): The input query used to search the Pinecone index for vectors.
        k (int, optional): Indicates top results to choose. Default is 5.

    Returns:
        list: A list of results containing the most similar vectors from the Pinecone index.
    """
    
    results = pinecone_index.similarity_search(query, k=k)
    return results

def response_generator(query):
    """
    Generates a response to the given query by retrieving relevant information from the Pinecone index and invoking 
    a processing chain with llm.

    Args:
        query (str): The user's input or question that will be used to retrieve relevant information and generate a response.

    Returns:
        str: The generated response to the query, either based on the retrieved information or an error messageif the process fails.
    """
    
    try:
        results = retrieve_response_from_pinecone(query)
        print("results", results)

        # Generating a response by invoking the chain with retrieved content and the original query
        answer = chain.invoke(input={"content": results, "input": query})
    except Exception as e:
        # Returning an error message if any exception occurs
        answer = f"Sorry, I am unable to find the answer to your query. Please try again later. The error is {e}"
    
    return answer

app = FastAPI()

@app.get("/get_response/{query}")
async def root(query: str):
    """
    FastAPI endpoint to handle GET requests and return a generated response for a user's query.

    Args:
        query (str): The query string input from the user, passed as a path parameter in the API request.

    Returns:
        dict: A dictionary containing the response generated from the query.
    """
    
    print("User_query : " + query)
    return response_generator(query)


if __name__ == "__main__":
    """
    Initializes the FastAPI server, loads environment variables, creates an embedding model and Pinecone index, 
    uploads a document for processing, and sets up a language model for generating responses.

    This block of code performs the following tasks:
    - Loads environment variables.
    - Initializes the embedding model for document chunking and retrieval.
    - Creates a Pinecone index to store document embeddings.
    - Uploads a specific PDF document to the Pinecone index for later query-based retrieval.
    - Sets up a language model (LLM) for generating human-like responses.
    - Defines the system prompt and response behavior for the assistant.
    - Sets up a chain that combines document retrieval with response generation.
    - Starts the FastAPI server on host `0.0.0.0` at port 8000.
    """

    # Loading environment variables from .env file
    load_dotenv()

    # Initializing embedding model for creating document vectors
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # Pinecone index name for storing document embeddings
    index_name = "sarvam-ai-assessment"

    # Creating Pinecone index using the embedding model
    pinecone_index = creating_pinecone_index(embedding)

    # Uploading a PDF document for processing and storing chunks in the Pinecone index
    uploading_document_to_pinecone("./data/ncert_data.pdf")

    # Initializing the LLM with the 'gemini-1.5-flash' model and a specified temperature for response generation
    llm = GoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)

    # Defining a system prompt for how the assistant should behave when answering questions
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved content to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. I am a student and I want a simple and precise answer to my query."
        "The answer should be in 100 words."
        "\n\n"
        "{content}"
    )

    # Creating a prompt template for generating responses based on retrieved content and human input
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ],
    )

    # Setting up the document processing chain for response generation based on retrieved documents
    chain = create_stuff_documents_chain(llm, prompt, document_variable_name="content")

    # Starting the FastAPI server with Uvicorn, accessible at 0.0.0.0 on port 8000
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)