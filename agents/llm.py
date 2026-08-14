import os
from dotenv import load_dotenv
load_dotenv()

def get_llm():
    """
    Returns LLM instance.
    Uses Groq if API key available, else falls back to Ollama.
    """
    groq_key = os.getenv("GROQ_API_KEY")

    if groq_key:
        from langchain_groq import ChatGroq
        print("Using Groq API (llama-3.2-3b-preview)")
        return ChatGroq(
            model="llama-3.2-3b-preview",
            temperature=0,
            api_key=groq_key
        )
    else:
        from langchain_ollama import ChatOllama
        print("Using local Ollama (llama3.2)")
        return ChatOllama(model="llama3.2", temperature=0)