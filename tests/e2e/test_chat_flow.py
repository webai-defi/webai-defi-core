import requests
import uuid
import time
from typing import List, Dict

BASE_URL = "http://localhost:3011/api"

def test_chat_flow():
    # Create test data
    wallet_id = "test_wallet_" + str(uuid.uuid4())
    chat_uuid = str(uuid.uuid4())
    
    # Step 1: Create new user
    response = requests.post(
        f"{BASE_URL}/user/",
        json={"wallet_id": wallet_id}
    )
    assert response.status_code == 200
    assert response.json()["wallet_id"] == wallet_id
    
    # Step 2: Login/Get user
    response = requests.get(f"{BASE_URL}/user/{wallet_id}")
    assert response.status_code == 200
    assert response.json()["wallet_id"] == wallet_id
    
    # Step 3: Generate chat response
    messages = [{"role": "user", "content": "What is Python?"}]
    response = requests.post(
        f"{BASE_URL}/chat/generate",
        json={"messages": messages}
    )
    assert response.status_code == 200
    answer = response.text
    
    # Step 4: Create chat thread
    response = requests.post(
        f"{BASE_URL}/user/chats/",
        params={"wallet_id": wallet_id},
        json={
            "uuid": chat_uuid,
            "name": "Test Chat",
            "question": messages[0]["content"],
            "answer": answer
        }
    )
    assert response.status_code == 200
    
    # Step 5: Get all user chats
    response = requests.get(
        f"{BASE_URL}/user/chats/",
        params={"wallet_id": wallet_id}
    )
    assert response.status_code == 200
    chats = response.json()
    assert len(chats) > 0
    assert any(chat["uuid"] == chat_uuid for chat in chats)
    
    # Step 6: Get chat history
    response = requests.get(f"{BASE_URL}/user/chats/{chat_uuid}")
    assert response.status_code == 200
    history = response.json()
    assert len(history) > 0
    assert history[0]["question"] == messages[0]["content"]
    assert history[0]["answer"] == answer

if __name__ == "__main__":
    test_chat_flow()
    print("All tests passed successfully!") 