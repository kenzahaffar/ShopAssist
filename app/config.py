import os
from dotenv import load_dotenv

load_dotenv()

MODE = os.getenv("MODE", "mock")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

if MODE not in ["mock", "real"]:
    raise ValueError("MODE doit être mock ou real")