import pytest
from unittest.mock import AsyncMock, MagicMock
from src.entry import on_fetch
import json

@pytest.mark.asyncio
async def test_on_fetch_invalid_json():
    # Mock request with invalid json
    request = AsyncMock()
    request.json.side_effect = Exception("Invalid JSON")
    
    response = await on_fetch(request, None)
    assert response["status"] == 400
    assert response["message"] == "Invalid JSON mapping"

@pytest.mark.asyncio
async def test_on_fetch_no_message():
    # Mock request with valid JSON but no message key
    request = AsyncMock()
    request.json.return_value = {"other": "data"}
    
    response = await on_fetch(request, None)
    assert response["status"] == 200
    assert response["message"] == "Not a message update"

@pytest.mark.asyncio
async def test_on_fetch_no_text():
    # Mock request with valid JSON, message key, but no text
    request = AsyncMock()
    request.json.return_value = {"message": {"chat": {"id": 123}}}
    
    response = await on_fetch(request, None)
    assert response["status"] == 200
    assert response["message"] == "No text provided"
