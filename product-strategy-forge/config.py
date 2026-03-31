import os
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from agents import OpenAIChatCompletionsModel
from agents import set_tracing_disabled

load_dotenv()
set_tracing_disabled(True)

MAX_TURNS = int(os.getenv("MAX_TURNS", "40"))

# Azure OpenAI client
_azure_client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

# Model object that the agents SDK can use
MODEL = OpenAIChatCompletionsModel(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    openai_client=_azure_client,
)
