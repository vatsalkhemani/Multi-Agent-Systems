import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from agents import set_tracing_disabled

# Load .env from this directory, then parent (root) for shared keys like GEMINI_API_KEY
_this_dir = Path(__file__).resolve().parent
load_dotenv(_this_dir / ".env")
load_dotenv(_this_dir.parent / ".env")  # root .env as fallback
set_tracing_disabled(True)

MAX_TURNS = int(os.getenv("MAX_TURNS", "50"))

# ── Azure OpenAI (GPT-4o) — used by all agents except Reviewer ──
_azure_client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

MODEL = OpenAIChatCompletionsModel(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    openai_client=_azure_client,
)

# ── Google Gemini (Trip Reviewer) — different provider for genuine second opinion ──
_gemini_client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

GEMINI_MODEL = OpenAIChatCompletionsModel(
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    openai_client=_gemini_client,
)
