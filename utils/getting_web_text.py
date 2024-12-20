import bs4
import os
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

os.environ["USER_AGENT"] = "dd"

page_url = "https://www.geeksforgeeks.org/introduction-machine-learning/"

strainer = bs4.SoupStrainer(["article", "main"])

loader = WebBaseLoader(
    web_path = page_url,
    bs_kwargs = {"parse_only": strainer},
)

document = loader.load()
document[0].page_content = document[0].page_content.replace("\n\n\n", " ").strip()
document[0].page_content = document[0].page_content.replace("\n\n", " ").strip()

splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 80)

splitted_docs = splitter.split_documents(document)

print("ALL DONE")

# print(f"{doc.metadata}\n")
# print(doc.page_content[:500])