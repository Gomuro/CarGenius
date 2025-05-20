# import pytest
# from httpx import AsyncClient, ASGITransport
# from app.main import app
#
# @pytest.mark.asyncio
# async def test_health_check():
#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
#         response = await ac.get("/")
#     assert response.status_code == 200
#     assert response.json() == {"status": "ok"}





# from fastapi import FastAPI
# from starlette.testclient import TestClient
#
# from app.tests.conftest import app
#
# client = TestClient(app)
#
#
# def test_read_root():
#     response = client.get("/")
#     assert response.status_code == 200
#     assert response.json() == {"message": "Welcome to CarGenius API"}
