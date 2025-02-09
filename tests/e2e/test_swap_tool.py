import requests
from typing import Generator

BASE_URL = "http://localhost:3011/api"

def read_stream_response(response: requests.Response) -> str:
    """Read streaming response"""
    return "".join(chunk.decode("utf-8") for chunk in response.iter_content(chunk_size=128))

def test_swap_tool_called():
    """Test that swap request triggers correct tool call"""
    input_message = "Swap BTC to SOL"
    
    response = requests.post(
        f"{BASE_URL}/chat/generate",
        json={"messages": [{"role": "user", "content": input_message}]},
        stream=True
    )
    
    assert response.status_code == 200
    received_response = read_stream_response(response)
    
    # Обновленные проверки
    assert "TokenSwap" in received_response
    assert "I've prepared the swap interface" in received_response
    assert '"type":"swap"' in received_response
    assert '"swapA": "BTC"' in received_response  # Проверяем точное значение
    assert '"swapB": "SOL"' in received_response   # Проверяем точное значение
    assert "amount" not in received_response

if __name__ == "__main__":
    test_swap_tool_called()
    print("Swap test passed successfully!") 