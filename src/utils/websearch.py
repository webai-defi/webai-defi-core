import httpx
from dotenv import load_dotenv
import os

load_dotenv()

YOUCOM_API_KEY = os.getenv("YOUCOM_API_KEY")

def ai_websearch(query):
    headers = {"X-API-Key": YOUCOM_API_KEY}
    params = {"query": query}
    with httpx.Client() as client:
        response = client.get(
            f"https://api.ydc-index.io/search",
            params=params, 
            headers=headers,
        )
        return response.json()
    
results = ai_websearch("reasons to smile")
print(results)