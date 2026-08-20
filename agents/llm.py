import os
from dotenv import load_dotenv
load_dotenv()

def get_llm():
    groq_key = os.getenv("GROQ_API_KEY")

    if groq_key:
        from langchain_groq import ChatGroq
        print("Using Groq API (llama3-8b-8192)")
        return ChatGroq(
            model="llama3-8b-8192",
            temperature=0,
            api_key=groq_key
        )
    else:
        from langchain_ollama import ChatOllama
        print("Using local Ollama (llama3.2)")
        return ChatOllama(model="llama3.2", temperature=0)