from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from langchain_community.tools import DuckDuckGoSearchResults

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
import requests
import re
import random

# Class to define the schema for the greeting tool
class GreetingTool(BaseModel):
    """
    This is class that defines the schema for the greeting tool.

    Attributes:
        query (str): The user's input string, representing a greeting query.
    """
    query: str = Field(title="Query", description="A greeting query to be processed.")
    # profession: str = Field(title="profession", description="profession of the user asking query.")
    

# Function to process greeting queries
def greeting_tool(query: str) -> str:
    """
    This function Processes user's greeting query and responds appropriately.

    Args:
        query (str): The user's input, which will contain a greeting text.

    Returns:
        str: A response to the user's greeting, or a general introduction if no greeting is found.
    """
    return llm.invoke(query)


# Creating a structured tool from the greeting function
greeting = StructuredTool.from_function(
    func=greeting_tool,
    name="Greetings",
    description="A tool for handling greeting queries.",
    args_schema=GreetingTool,
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
    # profession: str = Field(title="profession", description="profession of the user asking query.")
    

# Function to call the Vector Database and retrieve a response
def calling_database(query) -> str:
    """
    Calls Vector Database with the user's query to retrieve relevant content from the PDF.

    Args:
        query (str): The user's input query that will be sent to the Vector Database for processing.

    Returns:
        str: The text response from the Vector Database after processing the query.
    """
    # print("\n\nquery : ", query)
    query_pattern = r'query:"(.*?)"'
    profession_pattern = r'profession:"(\S+)'

    # Use re.search to find matches
    query_match = re.search(query_pattern, query)
    profession_match = re.search(profession_pattern, query)

    # Extract values if matches are found
    query = query_match.group(1) if query_match else None
    profession = profession_match.group(1) if profession_match else None
    # print("query : ", query, " and profession : ", profession)
    # response = {"success":"Success"}
    response = requests.get(f"http://0.0.0.0:8000/get_response", params={"query": query, "profession": profession}).json()
    return response


# Creating a structured tool for calling the database
db_calling = StructuredTool.from_function(
    func=calling_database,
    name="Database Call",
    description="A tool for calling the Vector Database to answer queries related to the provided PDF content. Use this tool if you need any information regarding the pdf file.",
    args_schema=DbCall,
    return_direct=True
)

# Class to define the schema for handling unrelated queries
class SearchingWeb(BaseModel):
    """
    This is class that defines the schema for Searching Internet for any resources.

    Attributes:
        query (str): The user's input string, representing a non-related query.
    """
    query: str = Field(title="Query", description="A query not related to the topic of pdf file.")
    # profession: str = Field(title="profession", description="profession of the user asking query.")

# Function to process unrelated queries
def searching_web(query: str) -> list:
    """
    This function Processes user's unrelated query to provide some resources link.

    Args:
        query (str): The user's input, which will contain an unrelated query with topic of pdf file.

    Returns:
        resources (list): A list of resources to user's query. It contains Title and url of the resource.
    """
    search = DuckDuckGoSearchResults(safesearch = "on", max_results=10)

    # print("\n\nquery : ", query)
    query_pattern = r'query:"(.*?)"'

    # Use re.search to find matches
    query_match = re.search(query_pattern, query)

    # Extract values if matches are found
    query = query_match.group(1) if query_match else None

    results = search.invoke(query)

    try:

        # Regular expressions to match title and link
        title_pattern = r'title:\s*(.*?),\s*link:'
        link_pattern = r'link:\s*(https?://\S+)'

        # Extracting titles and links
        titles = re.findall(title_pattern, results)
        links = re.findall(link_pattern, results)

        # Combine titles and links
        results = list(zip(titles, links))
        random.shuffle(results)
        print(results)
        # print(len(results))
        return results[:4]

    except Exception as e:
        print(e)
        return e


# Creating a structured tool from the searching_web function
web_search = StructuredTool.from_function(
    func=searching_web,
    name="Web Searching",
    description="A tool for handling queries not related to topic of the pdf file.",
    args_schema=SearchingWeb,
    return_direct=True
)


# Initialize the agent with the tool
tools = [greeting, db_calling, web_search]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/to_agent")
async def root(query: str, profession: str):
    """
    FastAPI endpoint to handle GET requests and return a generated response for a user's query.

    Args:
        query (str): The query string input from the user, passed as a path parameter in the API request.

    Returns:
        dict: A dictionary containing the response generated from the query.
    """
    
    global description
    print("User_query : " + query)
    try:
        # print("profession : ", profession)
        agent_input = {"query": query, "description": description, "profession": profession}
        response = agent_executor.invoke(agent_input)
        return response
    except Exception as e:
        print(e)
        return e    
        

class DescriptionRequest(BaseModel):
    description: str

@app.post("/send_desc")
def send_desc(request: DescriptionRequest):
    """
    FastAPI endpoint to handle POST requests for sending the description of the document to the agent.

    Args:
        description (str): The description of the document that will be used by the agent to generate responses.

    Returns:
        dict: A dictionary containing the status of the document description process.
    """
    global description
    description = request.description
    # print("type(description)", type(description))
    print("Description : ", description)

if __name__ == "__main__":
    
    # Loading environment variables from the .env file
    load_dotenv()
    
    description = ""

    # Initializing the Google Generative AI (LLM) model with specific parameters for the agent
    llm = GoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)

    # Defining the prompt template for the agent to follow when answering questions
    template = '''You are a helpful chatbot. You answer to user query only if it is related to the information I am providing you at the end.
    You also consider the user's profession for better context when calling the Database tool.

    Answer the following questions as best you can. You have access to the following tools:
    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: query:"{query}" and profession:"{profession}"
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question
    Below this is a formatted information of the content.
    information {description}
    Begin!

    Question: {query} and I am a {profession}.
    Thought:{agent_scratchpad}'''

    # print("tools : ", tools)

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
