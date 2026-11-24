"""
USD per 1 million tokens: (input, output).

Ollama runs on your own machine, so its API cost is $0. To still give a
useful number, the report also prices the same tokens at a hosted
"reference" model. Llama 3.2 and 3.1 share a tokenizer, so counts carry over.

Groq prices change: check https://groq.com/pricing before publishing numbers.
"""
PRICES_PER_MILLION = {
    "llama3.2": (0.0, 0.0),                    # local Ollama
    "llama-3.1-8b-instant": (0.05, 0.08),      # Groq
    "llama-3.3-70b-versatile": (0.59, 0.79),   # Groq
}

REFERENCE_MODEL = "llama-3.1-8b-instant"


def cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    price_in, price_out = PRICES_PER_MILLION.get(model, (0.0, 0.0))
    return (prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000


def reference_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    return cost_usd(REFERENCE_MODEL, prompt_tokens, completion_tokens)