import requests
import uuid
from unittest.mock import patch

BASE_URL = "http://localhost:3011/api/toolcall"

def test_get_market_chart():
    """Test fetching market chart with a valid mint address and interval"""
    mint_address = str(uuid.uuid4())  # Simulate a random mint address
    interval = "1m"

    response = requests.get(f"{BASE_URL}/market-chart", params={"mint_address": mint_address, "interval": interval})
    assert response.status_code == 200
    assert "data" in response.json()

def test_get_market_chart_invalid_interval():
    """Test fetching market chart with an invalid interval"""
    mint_address = str(uuid.uuid4())
    interval = "invalid_interval"

    response = requests.get(f"{BASE_URL}/market-chart", params={"mint_address": mint_address, "interval": interval})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid interval parameter"


def test_get_pumpfun_top_tokens():
    """Test fetching top tokens"""
    response = requests.get(f"{BASE_URL}/pumpfun-top-tokens")
    assert response.status_code == 200
    assert "data" in response.json()


if __name__ == "__main__":
    test_get_market_chart()
    test_get_market_chart_invalid_interval()
    test_get_pumpfun_top_tokens()
    print("All tests passed successfully!")
