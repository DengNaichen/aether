
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List

# Load env
project_root = Path(__file__).parent.parent
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

class Node(BaseModel):
    name: str
    description: str

class Graph(BaseModel):
    nodes: List[Node]

def test_model():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("No API Key found")
        return

    print(f"Testing gemini-3-pro-preview with API Key: {api_key[:5]}...")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        temperature=0,
        google_api_key=api_key
    )
    structured_llm = llm.with_structured_output(Graph)

    try:
        result = structured_llm.invoke("Extract nodes from: The sky is blue and the grass is green.")
        print("Result:", result)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_model()
