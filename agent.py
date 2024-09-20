from fastapi import FastAPI

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
import requests

# Class to define the schema for the greeting tool
class GreetingTool(BaseModel):
    """
    This is class that defines the schema for the greeting tool.

    Attributes:
        query (str): The user's input string, representing a greeting query.
    """
    query: str = Field(title="Query", description="A greeting query to be processed.")
    

# Function to process greeting queries
def greeting_tool(query: str) -> str:
    """
    This function Processes user's greeting query and responds appropriately.

    Args:
        query (str): The user's input, which will contain a greeting text.

    Returns:
        str: A response to the user's greeting, or a general introduction if no greeting is found.
    """
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
    lower_query = query.lower()

    # Check if any common greeting is in the user's query
    if any(greeting in lower_query for greeting in greetings):
        return "Hello! How can I assist you today?"
    else:
        return "Nice to have a conversation with you. I am your assistant to help you with the topic of Sound. Please ask me anything related to it."


# Creating a structured tool from the greeting function
greeting = StructuredTool.from_function(
    func=greeting_tool,
    name="Greetings",
    description="A tool for handling greeting queries.",
    args_schema=GreetingTool,
    return_direct=True
)


# Class to define the schema for handling unusual queries
class UnusualQuery(BaseModel):
    """
    A class that defines the schema for handling unusual queries.

    This class inherits from `BaseModel` and defines the structure of the query, which is not related to the PDF content.
    The query field includes a title and description to provide metadata for the tool.

    Attributes:
        query (str): The user's input string, representing a query unrelated to the provided content.
    """
    query: str = Field(title="Query", description="A query not related to the pdf content.")
    

# Function to handle queries that are not related to the provided content
def unusual_query_handler(query: str) -> str:
    """
    Handles queries that are  not related to the provided PDF content.

    Args:
        query (str): The user's input, which is determined to be not related to the PDF content.

    Returns:
        str: A prompt asking the user to ask questions related to the topic of sound.
    """
    return "Please ask a question related to the topic Sound."


# Creating a structured tool from the unusual query handler function
unusual_query = StructuredTool.from_function(
    func=unusual_query_handler,
    name="Unusual Query Handler",
    description="A tool for handling queries that are not related to the provided sound-related PDF.",
    args_schema=UnusualQuery,
    return_direct=True
)

# Class to define the schema for handling database calls
class DbCall(BaseModel):
    """
    This class defines the schema for making calls to the Vector Database.

    Attributes:
        query (str): The user's input string, represents a query to be processed by calling the Vector Database.
    """
    query: str = Field(title="Query", description="A query to be processed by calling the Vector Database.")
    

# Function to call the Vector Database and retrieve a response
def calling_database(query: str) -> str:
    """
    Calls Vector Database with the user's query to retrieve relevant content from the PDF.

    Args:
        query (str): The user's input query that will be sent to the Vector Database for processing.

    Returns:
        str: The text response from the Vector Database after processing the query.
    """
    print("calling_database")
    response = requests.get(f"http://localhost:8000/get_response/{query}")
    return response.text


# Creating a structured tool for calling the database
db_calling = StructuredTool.from_function(
    func=calling_database,
    name="Database Call",
    description="A tool for calling the Vector Database to answer queries related to the provided PDF content. "
                "The PDF details are: Title=Chapter 11 Sound, Author=NCERT, Subject=Physics, Class=11, Board=CBSE.",
    args_schema=DbCall,
    return_direct=True
)

# Initialize the agent with the tool
tools = [greeting, db_calling, unusual_query]

app = FastAPI()

@app.get("/to_agent/{query}")
async def root(query: str):
    """
    FastAPI endpoint to handle GET requests and return a generated response for a user's query.

    Args:
        query (str): The query string input from the user, passed as a path parameter in the API request.

    Returns:
        dict: A dictionary containing the response generated from the query.
    """
    
    print("User_query : " + query)
    response = agent_executor.invoke({"input": query})
    return response

if __name__ == "__main__":
    
    # Loading environment variables from the .env file
    load_dotenv()
    
    # Initializing the Google Generative AI (LLM) model with specific parameters for the agent
    llm = GoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)

    # Defining the prompt template for the agent to follow when answering questions
    template = '''Answer the following questions as best you can. You have access to the following tools:

    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought:{agent_scratchpad}'''

    # Creating a prompt template object from the defined template
    prompt = PromptTemplate.from_template(template)

    # Initializing an agent that uses the LLM and tools to respond to user queries
    # The tools variable is a list of structured tools that the agent can invoke
    agent = create_react_agent(llm, tools, prompt)

    # The agent_executor is responsible for executing the agent and managing tool usage
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Starting the FastAPI server using Uvicorn, making the app accessible at 0.0.0.0 on port 8080
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)