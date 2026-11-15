from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from main import app
from repositories.moderation import ModerationRepository
from routers.predict import get_service
from schemas import Advertisement
from services.moderation import ModerationService


@pytest.fixture
def payload():
    return dict(seller_id=1, is_verified_seller=False, item_id=2,
                name="Bicycle", description="Good condition", category=3, images_qty=0)


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.parametrize("verified,images,expected", [
    (True, 0, False), (True, 1, False), (False, 0, True),
    (False, 1, False), (False, 10, False),
])
def test_predict(client, payload, verified, images, expected):
    payload.update(is_verified_seller=verified, images_qty=images)
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json() is expected
    assert ModerationService(ModerationRepository()).predict(Advertisement(**payload)) is expected


@pytest.mark.parametrize("field", ["seller_id", "is_verified_seller", "item_id",
                                  "name", "description", "category", "images_qty"])
def test_missing_field(client, payload, field):
    del payload[field]
    assert client.post("/predict", json=payload).status_code == 400


@pytest.mark.parametrize("field,value", [
    ("seller_id", "1"), ("seller_id", True), ("seller_id", 0),
    ("item_id", -1), ("item_id", 1.5), ("category", "3"), ("category", 0),
    ("images_qty", -1), ("images_qty", "1"), ("images_qty", False),
    ("is_verified_seller", "true"), ("is_verified_seller", 1),
    ("name", 123), ("name", ""), ("name", "   "),
    ("description", []), ("description", ""), ("description", None),
])
def test_invalid_field(client, payload, field, value):
    payload[field] = value
    assert client.post("/predict", json=payload).status_code == 400


def test_invalid_body(client, payload):
    assert client.post("/predict").status_code == 400
    assert client.post("/predict", content="{", headers={"Content-Type": "application/json"}).status_code == 400
    assert client.post("/predict", json={**payload, "extra": 1}).status_code == 400


def test_business_error(client, payload):
    service = Mock(spec=ModerationService)
    service.predict.side_effect = RuntimeError("secret implementation details")
    app.dependency_overrides[get_service] = lambda: service
    response = client.post("/predict", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_repository_error(client, payload):
    repository = Mock(spec=ModerationRepository)
    repository.minimum_images_for_unverified_seller.side_effect = RuntimeError("unavailable")
    app.dependency_overrides[get_service] = lambda: ModerationService(repository)
    assert client.post("/predict", json=payload).status_code == 500
