import os
from dotenv import load_dotenv
load_dotenv()

# Groq retires models regularly, so the name lives in .env instead of code.
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_OLLAMA_MODEL = "llama3.2"


def get_model_info() -> dict:
    """Which provider/model the agents will use. Used for trace metadata."""
    if os.getenv("GROQ_API_KEY"):
        return {"provider": "groq",
                "model": os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)}
    return {"provider": "ollama",
            "model": os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)}


def get_llm():
    info = get_model_info()

    if info["provider"] == "groq":
        from langchain_groq import ChatGroq
        print(f"Using Groq API ({info['model']})")
        return ChatGroq(model=info["model"], temperature=0,
                        api_key=os.getenv("GROQ_API_KEY"))

    from langchain_ollama import ChatOllama
    print(f"Using local Ollama ({info['model']})")
    return ChatOllama(model=info["model"], temperature=0,
                      base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))