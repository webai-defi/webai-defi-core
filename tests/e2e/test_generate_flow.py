import requests
import uuid
from unittest.mock import patch

BASE_URL = "http://localhost:3011/api/chat/generate"


def read_stream_response(response):
    """Helper function to read a streamed response"""
    full_response = ""
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            full_response += chunk.decode('utf-8')
    return full_response


def test_mocked_config_response():
    """Test that a predefined question returns the expected response from the config"""
    input_message = "  how to buy bitcoin"  # Matches mock_chats_config.py
    expected_response = "very easy, ligma balls"

    response = requests.post(BASE_URL, json={"messages": [{"role": "user", "content": input_message}]}, stream=True)

    assert response.status_code == 200
    received_response = read_stream_response(response)
    assert expected_response in received_response, f"Expected '{expected_response}', got '{received_response}'"


def test_chart_tool_called():
    """Test that a request requiring a chart triggers the ChartDetails tool"""
    input_message = "Show me the chart for 2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump"

    response = requests.post(BASE_URL, json={"messages": [{"role": "user", "content": input_message}]}, stream=True)

    assert response.status_code == 200
    received_response = read_stream_response(response)

    assert "2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump" in received_response
    assert "ChartDetails" in received_response


def test_multiple_tool_calls():
    """Test that a request requiring multiple tools triggers all necessary tool calls"""
    input_message = "Find news about Bitcoin and show me the chart for 2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump"

    response = requests.post(BASE_URL, json={"messages": [{"role": "user", "content": input_message}]}, stream=True)

    assert response.status_code == 200
    received_response = read_stream_response(response)

    assert "2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump" in received_response
    assert "ChartDetails" in received_response
    assert "WebSearch" in received_response


if __name__ == "__main__":
    test_mocked_config_response()
    test_chart_tool_called()
    test_multiple_tool_calls()
    print("All tests passed successfully!")
