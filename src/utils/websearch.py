import httpx
from dotenv import load_dotenv
import os

load_dotenv()

YOUCOM_API_KEY = os.getenv("YOUCOM_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

async def ai_websearch(query):
    # Check if API key exists
    if not YOUCOM_API_KEY:
        raise ValueError("YOUCOM_API_KEY not found in environment variables")
    
    headers = {"X-API-Key": YOUCOM_API_KEY}
    params = {"query": query}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.ydc-index.io/search",
                params=params, 
                headers=headers,
                timeout=30  # Add timeout for safety
            )
            response.raise_for_status()  # Raise exception for bad status codes
            return response.json()
    except httpx.HTTPError as e:
        raise Exception(f"Error during API request: {str(e)}")
    
async def perplexity_search(query):
    # Check if API key exists
    if not PERPLEXITY_API_KEY:
        raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "pplx-7b-online",  # Using online model for web search
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "return_citations": True,  # Get source links
        "search_recency_filter": "month"  # Get recent results
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "answer": result["choices"][0]["message"]["content"],
                "citations": result.get("citations", [])
            }
    except httpx.HTTPError as e:
        raise Exception(f"Error during Perplexity API request: {str(e)}")
    
async def deep_research_topic(topic, time_range="day"):
    """
    Performs deep research on a topic using Perplexity API
    time_range: 'day' or 'week'
    """
    if not PERPLEXITY_API_KEY:
        raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
    
    # Construct research prompts
    prompts = [
        f"Provide the latest {time_range}'s comprehensive analysis and developments about {topic}",
        f"What are the most significant recent discussions and trends about {topic} in the last {time_range}?",
        f"What are the expert opinions and critical insights about {topic} from the last {time_range}?"
    ]
    
    results = []
    for prompt in prompts:
        try:
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "pplx-7b-online",
                "messages": [{"role": "user", "content": prompt}],
                "return_citations": True,
                "search_recency_filter": "day" if time_range == "day" else "week"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=45
                )
                response.raise_for_status()
                
                result = response.json()
                results.append({
                    "query": prompt,
                    "answer": result["choices"][0]["message"]["content"],
                    "citations": result.get("citations", [])
                })
                
        except httpx.HTTPError as e:
            raise Exception(f"Error during deep research: {str(e)}")
    
    return results

async def web_deep_search(query, search_type="comprehensive"):
    """
    Performs deep web search using Perplexity API
    search_type: 'comprehensive' or 'focused'
    """
    if not PERPLEXITY_API_KEY:
        raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
    
    # Adjust the search approach based on type
    if search_type == "comprehensive":
        system_prompt = (
            "Conduct a comprehensive web search and analysis. "
            "Include various perspectives, verified facts, and detailed information. "
            "Focus on credible sources and recent developments."
        )
    else:  # focused
        system_prompt = (
            "Provide a focused and specific answer based on the most relevant "
            "and authoritative sources. Prioritize accuracy and conciseness."
        )
    
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "pplx-7b-online",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "return_citations": True,
            "search_recency_filter": "month",
            "temperature": 0.1  # Lower temperature for more focused results
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=45
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "answer": result["choices"][0]["message"]["content"],
                "citations": result.get("citations", [])
            }
            
    except httpx.HTTPError as e:
        raise Exception(f"Error during web deep search: {str(e)}")
    


# How to use 
"""
# Глубокий анализ темы за последний день
results = await deep_research_topic("Bitcoin price movement", time_range="day")

# Всесторонний поиск по интернету
comprehensive = await web_deep_search("Impact of AI on cryptocurrency trading", search_type="comprehensive")

# Сфокусированный поиск
focused = await web_deep_search("Current Bitcoin mining difficulty", search_type="focused")
"""