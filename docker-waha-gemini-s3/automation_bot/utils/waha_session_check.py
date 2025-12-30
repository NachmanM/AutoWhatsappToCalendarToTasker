import os
import requests
from dotenv import load_dotenv

def waha_session_check():
    load_dotenv()
    WAHA_API_KEY = os.getenv("WAHA_API_KEY")
    WAHA_BASE_URL = os.getenv("WAHA_BASE_URL")

    headers = {"X-API-KEY": WAHA_API_KEY, "accept": "application/json"}

    response = requests.get(f'{WAHA_BASE_URL}/api/sessions?all=true', headers=headers)

    json_response = response.json()

    print(response.text)
    return json_response[0]["status"]
    
if __name__ == "__main__":
    waha_session_check()
