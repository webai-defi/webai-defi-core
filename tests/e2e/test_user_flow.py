import requests
import uuid
import time
from typing import List, Dict

BASE_URL = "http://localhost:3011/api"


def test_create_user():
    """Test creating a new user with a unique wallet_id"""
    wallet_id = f"test_wallet_{uuid.uuid4()}"

    response = requests.post(
        f"{BASE_URL}/user/",
        json={"wallet_id": wallet_id}
    )
    assert response.status_code == 200
    assert response.json()["wallet_id"] == wallet_id

    # Try creating the same user again (should fail)
    response = requests.post(
        f"{BASE_URL}/user/",
        json={"wallet_id": wallet_id}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User with this wallet_id already exists"


def test_get_user():
    """Test retrieving a user"""
    wallet_id = f"test_wallet_{uuid.uuid4()}"

    # Create user
    requests.post(
        f"{BASE_URL}/user/",
        json={"wallet_id": wallet_id}
    )

    # Fetch the user
    response = requests.get(f"{BASE_URL}/user/{wallet_id}")
    assert response.status_code == 200
    assert response.json()["wallet_id"] == wallet_id

    # Fetch non-existing user (should return 404)
    response = requests.get(f"{BASE_URL}/user/nonexistent_wallet")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_chats():
    """Test retrieving chats for a user"""
    wallet_id = f"test_wallet_{uuid.uuid4()}"

    # Create user
    requests.post(
        f"{BASE_URL}/user/",
        json={"wallet_id": wallet_id}
    )

    # Fetch chats (should be empty)
    response = requests.get(
        f"{BASE_URL}/user/chats/",
        params={"wallet_id": wallet_id}
    )
    assert response.status_code == 200
    assert response.json() == []  # No chats initially

if __name__ == "__main__":
    test_create_user()
    test_get_user()
    test_get_chats()
    print("All tests passed successfully!")