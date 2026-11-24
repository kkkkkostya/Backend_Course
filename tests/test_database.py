import os

import asyncpg
import httpx
import pytest

from database import DEFAULT_DATABASE_URL, get_pool
from main import app
from repositories.advertisements import AdvertisementRepository
from repositories.users import UserRepository
from schemas import AdvertisementCreate, UserCreate

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


@pytest.fixture
async def connection():
    connection = await asyncpg.connect(os.getenv("TEST_DATABASE_URL", DEFAULT_DATABASE_URL))
    transaction = connection.transaction()
    await transaction.start()
    try:
        yield connection
    finally:
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def user(connection):
    data = UserCreate(first_name="Ivan", last_name="Petrov", violations_qty=2)
    user_id = await UserRepository(connection).create(data)
    return user_id, data


@pytest.fixture
async def advertisement(connection, user):
    data = AdvertisementCreate(seller_id=user[0], name="Bicycle",
                               description="Good condition", category=3, images_qty=0)
    item_id = await AdvertisementRepository(connection).create(data)
    return item_id, data


async def test_create_user(connection, user):
    user_id, data = user
    row = await connection.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    assert user_id > 0
    assert dict(row) == {"id": user_id, **data.model_dump()}


async def test_create_advertisement(connection, advertisement):
    item_id, data = advertisement
    row = await connection.fetchrow("SELECT * FROM advertisements WHERE id = $1", item_id)
    assert item_id > 0
    assert dict(row) == {"id": item_id, **data.model_dump()}
    prediction_data = await AdvertisementRepository(connection).get_for_prediction(item_id)
    assert prediction_data.model_dump() == {
        **data.model_dump(), "item_id": item_id, "is_verified_seller": False,
    }


@pytest.mark.parametrize("verified,images,expected", [
    (False, 0, True), (False, 1, False), (True, 0, False),
])
async def test_simple_predict_from_database(connection, advertisement, verified, images, expected):
    item_id, data = advertisement
    await connection.execute("UPDATE users SET is_verified = $1 WHERE id = $2",
                             verified, data.seller_id)
    await connection.execute("UPDATE advertisements SET images_qty = $1 WHERE id = $2",
                             images, item_id)

    def override_connection():
        return connection

    app.dependency_overrides[get_pool] = override_connection
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url="http://test") as client:
            response = await client.post("/simple_predict", json={"item_id": item_id})
        assert response.status_code == 200
        assert response.json() is expected
    finally:
        app.dependency_overrides.clear()


async def test_missing_advertisement(connection, advertisement):
    item_id, _ = advertisement
    await connection.execute("DELETE FROM advertisements WHERE id = $1", item_id)
    assert await AdvertisementRepository(connection).get_for_prediction(item_id) is None


async def test_application_pool(advertisement, monkeypatch):
    item_id, _ = advertisement
    monkeypatch.setenv("DATABASE_URL", os.getenv("TEST_DATABASE_URL", DEFAULT_DATABASE_URL))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url="http://test") as client:
            response = await client.post("/simple_predict", json={"item_id": item_id})
    assert response.status_code == 404
    assert response.json() == {"detail": "Advertisement not found"}
    assert app.state.db_pool.is_closing()


async def test_foreign_key(connection, advertisement):
    _, data = advertisement
    async with connection.transaction():
        missing_id = await UserRepository(connection).create(
            UserCreate(first_name="Temporary", last_name="Seller"))
        await connection.execute("DELETE FROM users WHERE id = $1", missing_id)
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        async with connection.transaction():
            await AdvertisementRepository(connection).create(data.model_copy(update={"seller_id": missing_id}))


@pytest.mark.parametrize("column,value", [("category", 0), ("images_qty", -1), ("name", " ")])
async def test_database_constraints(connection, advertisement, column, value):
    item_id, _ = advertisement
    with pytest.raises(asyncpg.CheckViolationError):
        async with connection.transaction():
            await connection.execute(f"UPDATE advertisements SET {column} = $1 WHERE id = $2",
                                     value, item_id)
