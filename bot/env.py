import os

try:
    from dotenv import load_dotenv

    load_dotenv("../.env")
except ImportError:
    print("dotenv not installed, skipping...")


WEBUI_URL = os.getenv("WEBUI_URL", "http://localhost:8080")
TOKEN = os.getenv("TOKEN", "")
OPENROUTER_API_KEY = ""
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
