from app import app, RepoCreate
import pytest


@pytest.asyncio
async def test_RepoCreate() -> None:
    test_client = app.test_client()
    response = await test_client.post("/repo/", json=RepoCreate("yolo"))
    data = await response.get_json()
    assert data == {"git_url": "yolo", "id": 1}
