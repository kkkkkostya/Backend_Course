from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from main import app
from database import get_pool
from repositories.advertisements import AdvertisementRepository
from routers.predict import get_advertisement_repository, get_service
from schemas import Advertisement
from services.moderation import ModerationService


@pytest.fixture
def repository():
    return AsyncMock(spec=AdvertisementRepository)


@pytest.fixture
def client(repository):
    app.dependency_overrides[get_advertisement_repository] = lambda: repository
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("verified,images,expected", [
    (False, 0, True), (False, 1, False), (True, 0, False), (True, 1, False),
])
def test_simple_predict(client, repository, verified, images, expected):
    repository.get_for_prediction.return_value = Advertisement(
        seller_id=1, item_id=2, is_verified_seller=verified,
        name="Bicycle", description="Good condition", category=3, images_qty=images,
    )
    response = client.post("/simple_predict", json={"item_id": 2})
    assert response.status_code == 200
    assert response.json() is expected
    repository.get_for_prediction.assert_awaited_once_with(2)


@pytest.mark.parametrize("body,loc", [
    ({}, ["body", "item_id"]),
    ({"item_id": 0}, ["body", "item_id"]),
    ({"item_id": -1}, ["body", "item_id"]),
    ({"item_id": "1"}, ["body", "item_id"]),
    ({"item_id": True}, ["body", "item_id"]),
    ({"item_id": 1.5}, ["body", "item_id"]),
    ({"item_id": None}, ["body", "item_id"]),
    ({"item_id": []}, ["body", "item_id"]),
    ({"item_id": 2147483648}, ["body", "item_id"]),
    ({"item_id": 1, "extra": 2}, ["body", "extra"]),
])
def test_invalid_item_id(client, repository, body, loc):
    response = client.post("/simple_predict", json=body)
    assert response.status_code == 400
    assert [error["loc"] for error in response.json()["detail"]] == [loc]
    repository.get_for_prediction.assert_not_awaited()


@pytest.mark.parametrize("body", [None, "{", "[]"])
def test_invalid_body(client, repository, body):
    response = client.post("/simple_predict", content=body,
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json()["detail"][0]["loc"][0] == "body"
    repository.get_for_prediction.assert_not_awaited()


@pytest.mark.parametrize("item_id", [1, 2147483647])
def test_missing_advertisement(client, repository, item_id):
    repository.get_for_prediction.return_value = None
    response = client.post("/simple_predict", json={"item_id": item_id})
    assert response.status_code == 404
    assert response.json() == {"detail": "Advertisement not found"}
    repository.get_for_prediction.assert_awaited_once_with(item_id)


def test_database_error(client, repository):
    repository.get_for_prediction.side_effect = RuntimeError("secret database details")
    response = client.post("/simple_predict", json={"item_id": 1})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_service_error(client, repository):
    service = Mock(spec=ModerationService)
    service.predict.side_effect = RuntimeError("secret service details")
    app.dependency_overrides[get_service] = lambda: service
    response = client.post("/simple_predict", json={"item_id": 1})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_invalid_id_does_not_query_database():
    pool = AsyncMock()
    app.dependency_overrides[get_pool] = lambda: pool
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post("/simple_predict", json={"item_id": 0})
        assert response.status_code == 400
        assert response.json()["detail"][0]["loc"] == ["body", "item_id"]
        pool.fetchrow.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()
