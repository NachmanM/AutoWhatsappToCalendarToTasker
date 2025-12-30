import os
from dotenv import load_dotenv
import requests
def waha_start_session():
    load_dotenv()

    WAHA_API_KEY = os.getenv("WAHA_API_KEY")
    WAHA_BASE_URL = os.getenv("WAHA_BASE_URL")

    headers = {"X-API-KEY": WAHA_API_KEY, "accept": "application/json"}

    response = requests.post(f"{WAHA_BASE_URL}/api/sessions/default/start", headers=headers)

    print(response)


if __name__ == "__main__":
    waha_start_session()
