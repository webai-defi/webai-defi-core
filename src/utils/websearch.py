import httpx
from dotenv import load_dotenv
import os

load_dotenv()

YOUCOM_API_KEY = os.getenv("YOUCOM_API_KEY")

def ai_websearch(query):
    # Check if API key exists
    if not YOUCOM_API_KEY:
        raise ValueError("YOUCOM_API_KEY not found in environment variables")
    
    headers = {"X-API-Key": YOUCOM_API_KEY}
    params = {"query": query}
    
    try:
        with httpx.Client() as client:
            response = client.get(
                "https://api.ydc-index.io/search",
                params=params, 
                headers=headers,
                timeout=30  # Add timeout for safety
            )
            response.raise_for_status()  # Raise exception for bad status codes
            return response.json()
    except httpx.HTTPError as e:
        raise Exception(f"Error during API request: {str(e)}")

# Remove test code from production file