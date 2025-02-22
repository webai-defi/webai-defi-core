"""Config"""
import os

from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

description = """
CryptoAgent API helps you do awesome stuff. 🚀

### How to use the API:

1. **Creating a user and chat:**
   - Send a POST request to `/api/user/chats/` with `wallet_id` parameters and JSON body containing `chat_uuid`, `question`, and `answer`. This will create a new chat and save it in the database.

2. **Getting the list of chats:**
   - Use a GET request to `/api/user/chats/` to get a list of all chats associated with your `wallet_id`.

3. **Getting chat history:**
   - Use a GET request to `/api/user/chats/{chat_uuid}/history` to get chat history in the format:
     ```json
     [
       {
         "question": "string",
         "answer": "string",
         "timestamp": "2025-01-26T18:47:58.953Z"
       }
     ]
     ```

### Example JavaScript for streaming text:
```javascript
async function streamText(url) {
    const response = await fetch(url);
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let result = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        result += decoder.decode(value, { stream: true });
        console.log(result); // print text to console
    }
}
```

"""


class Settings(BaseSettings):
    STREAMING: bool = True
    MODEL: str = "gpt-4o"
    TEMPERATURE: float = 0
    PROMPT: str = "hwchase17/openai-tools-agent"

    PROJECT_NAME: str = "Web Search Agent"
    PROJECT_DESC: str = description

    DEBUG_LOGS: bool = False
    LOGS_URL: str = "./logs"
    LOGS_FILE: str = "error.log"

    BITQUERY_API_KEY: str = os.environ["BITQUERY_API_KEY"]
    BITQUERY_URL: str = "https://streaming.bitquery.io/eap"

    TIME_INTERVALS: List[str] = ["1m", "5m", "15m", "30m", "60m", "1h", "4h", "6h", "8h", "12h", "1d", "3d", "7d", "30d"] # добавить

    MAX_NUM_OF_TOOLS: int = 1

    REDIS_HOST: str = os.environ["REDIS_HOST"]


settings = Settings()

os.makedirs(settings.LOGS_URL, exist_ok=True)
