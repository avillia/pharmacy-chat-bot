import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

PHARMACY_API_URL = os.getenv(
    'PHARMACY_API_URL',
    'https://67e14fb758cc6bf785254550.mockapi.io/pharmacies'
)

COMPANY_NAME = os.getenv('COMPANY_NAME', 'Pharmesol')
COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', 'contact@pharmesol.com')
COMPANY_PHONE = os.getenv('COMPANY_PHONE', '+1-555-PHARMA-1')

PROMPTS_DIR = os.getenv('PROMPTS_DIR', 'prompts')
DEFAULT_TIMEOUT = float(os.getenv('DEFAULT_TIMEOUT', '30.0'))
