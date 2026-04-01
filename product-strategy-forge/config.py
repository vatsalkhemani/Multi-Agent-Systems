import os
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from agents import set_tracing_disabled

load_dotenv()
set_tracing_disabled(True)

MAX_TURNS = int(os.getenv("MAX_TURNS", "40"))

# ── Azure OpenAI (GPT-4o) — used by all agents except Critic ──
_azure_client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

MODEL = OpenAIChatCompletionsModel(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    openai_client=_azure_client,
)

# ── Google Gemini (Critic) — different model provider for genuine second opinion ──
_gemini_client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

GEMINI_MODEL = OpenAIChatCompletionsModel(
    model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview"),
    openai_client=_gemini_client,
)
