# app/tests/test_gpt.py
import pytest
from sqlalchemy import delete
from app.models.car import ListingMobileDe, TechnicalDetails, Equipment
from app.models.gpt import GPTPromptLog
from unittest.mock import AsyncMock, patch
from app.models.license import LicenseKey


@pytest.mark.asyncio
async def test_gpt_ask(client, session):
    await session.execute(GPTPromptLog.__table__.delete())
    await session.execute(delete(ListingMobileDe))
    await session.execute(delete(TechnicalDetails))
    await session.execute(delete(Equipment))
    await session.commit()
    # Create a new LicenseKey instance with a test user ID and filters.
    # This represents a license record in the database that stores user preferences (filters).
    new_license = LicenseKey(
        key="test-user-123",
        filters=[
            {
                "brand": "Audi",
                "equipment": {},
                "technical_details": {}
            }
        ]
    )
    # Add the LicenseKey instance to the session and commit to save it in the test database.
    session.add(new_license)
    await session.commit()
    # Define the test user_id and GPT prompt (question).
    user_id = "test-user-123"
    test_prompt = "Which car will fit me?"
    # Define a mock response from the ML model for best car offers.
    best_price_offer = {
      "top_offers": [
        {
          "actual_price": 62980,
          "predicted_price": 75827.98,
          "saving": 12847.979999999996,
          "brand": "Audi",
          "model": "Q8 e-tron",
          "registration_year": 2024,
          "meleage": 7060,
          "color": "Grau",
          "url": "https://suchen.mobile.de/fahrzeuge/details.html?id=414311984&action=topInCategory&cn=DE&ms=1900%3B%3B%3B&od=up&ref=seo&refId=e9c3d823-068f-a924-a7fe-091857469190&s=Car&sb=rel&searchId=e9c3d823-068f-a924-a7fe-091857469190&vc=Car"
        }  ],
      "listings_count": 60
    }
    # Define a mock GPT response that will be returned instead of a real GPT call.
    mock_response = "Recommend Audi Q8 E-Tron with a price of 62980"

    # Mock the external calls to GPT client and ML best price search function:
    # - GPTClient.method returns the mock method response asynchronously.
    # patch(...) - temporarily replaces the original start_gpt, ml_best_price_search function with a fake(mock) version.
    #
    # new=AsyncMock(...) - creates an asynchronous mock (i.e., a function that can be awaiting) that always
    # returns {“top_offers”: best_price_offer}.
    #
    # This whole patch(...) is used in the with context, meaning that the substitution works only inside the with block,
    # and after leaving it, the function will be true again.
    with patch("app.services.gpt.GPTClient.start_gpt", new=AsyncMock(return_value=mock_response)), \
            patch("app.routers.gpt.ml_best_price_search", new=AsyncMock(return_value={
                "top_offers": best_price_offer["top_offers"],
                "listings_count": best_price_offer["listings_count"]
            })):
        # Send a POST request to the /api/v1/gpt/ask endpoint with the user ID,
        # prompt, filters (from the LicenseKey object), and empty chat history.
        response = await client.post("/api/v1/gpt/ask", json={
            "user_id": user_id,
            "gpt_prompt": test_prompt,
            "context": {"filters": new_license.filters},
            "chat_history": []
        })

    assert response.status_code == 200           # Check that the response status code is 200 OK
    data = response.json()                       # Parse the JSON response data
    assert data["user_id"] == user_id            # Check that the user_id in the response matches the test user_id
    assert data["gpt_prompt"] == test_prompt     # Check that the gpt_prompt in the response matches the test prompt
    assert data["gpt_response"] == mock_response # Check that the gpt_response in the response matches the mock response

    # Verify that the GPT prompt was saved to the database:
    # Execute a SELECT query on GPTPromptLog table filtering by user_id.
    logs = (await session.execute(
        GPTPromptLog.__table__.select().where(GPTPromptLog.user_id == user_id)
    )).fetchall()
    print(f"GPT logs for user {user_id}: {logs}")  # Print the fetched logs for debugging
    assert len(logs) == 1   # # Assert that exactly one GPT prompt record was saved for this user
    assert logs[0].gpt_prompt == test_prompt   # Assert that the saved GPT prompt matches the test prompt



@pytest.mark.asyncio
async def test_gpt_get_history(client, session):
    user_id = "test-user-123"
    # create fake records manually
    log = GPTPromptLog(
        user_id=user_id,
        gpt_prompt="Which crossover is better?",
        gpt_response="Mazda CX-5"
    )
    session.add(log)
    await session.commit()

    response = await client.get(f"/api/v1/gpt/history/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert "history" in data
    assert len(data["history"]) >= 2  # user + assistant
    assert data["count"] == len(data["history"])


@pytest.mark.asyncio
async def test_gpt_clear_history(client, session):
    user_id = "test-user-123"
    # add a few records
    session.add_all([
        GPTPromptLog(user_id=user_id, gpt_prompt="A?", gpt_response="B"),
        GPTPromptLog(user_id=user_id, gpt_prompt="C?", gpt_response="D"),
    ])
    await session.commit()

    # remove history
    response = await client.delete(f"/api/v1/gpt/history/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted_count"] >= 2

    # checking, that history is cleared
    remaining = (await session.execute(
        GPTPromptLog.__table__.select().where(GPTPromptLog.user_id == user_id)
    )).fetchall()   # fetch all records for the user
    assert len(remaining) == 0
    await session.execute(
        GPTPromptLog.__table__.delete().where(GPTPromptLog.user_id == user_id)
    )
