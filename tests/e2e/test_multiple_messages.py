import requests
import uuid
from typing import List, Dict

BASE_URL = "http://localhost:3011/api"

def read_stream_response(response):
    full_response = ""
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            full_response += chunk.decode('utf-8')
    return full_response

def test_multiple_messages_flow():
    # Create unique test wallet id
    wallet_id = f"mytest_{str(uuid.uuid4())}"
    chat_uuid = str(uuid.uuid4())

    # Step 1: Create new user and verify
    response = requests.post(
        f"{BASE_URL}/user/",
        json={"wallet_id": wallet_id}
    )
    assert response.status_code == 200
    
    response = requests.get(f"{BASE_URL}/user/{wallet_id}")
    assert response.status_code == 200
    assert response.json()["wallet_id"] == wallet_id

    # Step 2: Get initial chats (should be empty)
    response = requests.get(
        f"{BASE_URL}/user/chats/",
        params={"wallet_id": wallet_id}
    )
    assert response.status_code == 200
    initial_chats = response.json()
    assert len(initial_chats) == 0

    # Step 3: First message - Generate response with streaming
    first_message = "What is artificial intelligence? You can use websearch to get the answer."
    response = requests.post(
        f"{BASE_URL}/chat/generate",
        json={"messages": [{"role": "user", "content": first_message}]},
        stream=True
    )
    assert response.status_code == 200
    first_answer = read_stream_response(response)

    # Step 4: Save first Q/A pair
    response = requests.post(
        f"{BASE_URL}/user/chats/",
        params={"wallet_id": wallet_id},
        json={
            "uuid": chat_uuid,
            "name": "AI Discussion",
            "question": first_message,
            "answer": first_answer
        }
    )
    assert response.status_code == 200

    # Step 5: Second message - Generate response with streaming
    second_message = "Can you give some examples of AI applications?"
    response = requests.post(
        f"{BASE_URL}/chat/generate",
        json={
            "messages": [
                {"role": "user", "content": first_message},
                {"role": "assistant", "content": first_answer},
                {"role": "user", "content": second_message}
            ]
        },
        stream=True
    )
    assert response.status_code == 200
    second_answer = read_stream_response(response)

    # Step 6: Save second Q/A pair
    response = requests.post(
        f"{BASE_URL}/user/chats/",
        params={"wallet_id": wallet_id},
        json={
            "uuid": chat_uuid,
            "question": second_message,
            "answer": second_answer
        }
    )
    assert response.status_code == 200

    # Step 7: Get updated chat list
    response = requests.get(
        f"{BASE_URL}/user/chats/",
        params={"wallet_id": wallet_id}
    )
    assert response.status_code == 200
    updated_chats = response.json()
    assert len(updated_chats) == 1
    assert updated_chats[0]["uuid"] == chat_uuid

    # Step 8: Get and print chat history
    response = requests.get(f"{BASE_URL}/user/chats/{chat_uuid}")
    assert response.status_code == 200
    chat_history = response.json()
    
    print("\nChat History:")
    for message in chat_history:
        print(f"\nQuestion: {message['question']}")
        print(f"Answer: {message['answer']}")

    # Additional assertions
    assert len(chat_history) == 2
    assert chat_history[0]["question"] == first_message
    assert chat_history[0]["answer"] == first_answer
    assert chat_history[1]["question"] == second_message
    assert chat_history[1]["answer"] == second_answer

if __name__ == "__main__":
    test_multiple_messages_flow()
    print("\nAll tests passed successfully!") 