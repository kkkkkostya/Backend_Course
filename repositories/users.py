import asyncpg

from schemas import UserCreate


class UserRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def create(self, user: UserCreate) -> int:
        return await self.connection.fetchval(
            """INSERT INTO users (first_name, last_name, is_verified, violations_qty)
               VALUES ($1, $2, $3, $4) RETURNING id""",
            user.first_name, user.last_name, user.is_verified, user.violations_qty,
        )
