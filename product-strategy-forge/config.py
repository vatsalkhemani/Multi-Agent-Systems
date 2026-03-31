import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL", "gpt-4o")
MAX_TURNS = int(os.getenv("MAX_TURNS", "40"))
