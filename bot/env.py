import os

try:
    from dotenv import load_dotenv

    load_dotenv("../.env")
except ImportError:
    print("dotenv not installed, skipping...")


WEBUI_URL = os.getenv("WEBUI_URL", "http://localhost:8080")
TOKEN = os.getenv("TOKEN", "")
