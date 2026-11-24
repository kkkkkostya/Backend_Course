import asyncpg

from schemas import Advertisement, AdvertisementCreate


class AdvertisementRepository:
    def __init__(self, connection: asyncpg.Connection | asyncpg.Pool):
        self.connection = connection

    async def create(self, advertisement: AdvertisementCreate) -> int:
        return await self.connection.fetchval(
            """INSERT INTO advertisements
                   (seller_id, name, description, category, images_qty)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            advertisement.seller_id, advertisement.name, advertisement.description,
            advertisement.category, advertisement.images_qty,
        )

    async def get_for_prediction(self, item_id: int) -> Advertisement | None:
        row = await self.connection.fetchrow(
            """SELECT a.id AS item_id, a.seller_id, a.name, a.description,
                      a.category, a.images_qty, u.is_verified AS is_verified_seller
               FROM advertisements AS a
               JOIN users AS u ON u.id = a.seller_id
               WHERE a.id = $1""",
            item_id,
        )
        return Advertisement(**dict(row)) if row is not None else None
