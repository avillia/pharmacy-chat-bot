import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

PHARMACY_API_URL = os.getenv("PHARMACY_API_URL")
if not PHARMACY_API_URL:
    raise ValueError("PHARMACY_API_URL is not set")

COMPANY_NAME = os.getenv("COMPANY_NAME", "Pharmesol")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "contact@pharmesol.com")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+1-555-PHARMA-1")

PROMPTS_DIR = os.getenv("PROMPTS_DIR", "prompts")
DEFAULT_TIMEOUT = float(os.getenv("DEFAULT_TIMEOUT", "30.0"))
