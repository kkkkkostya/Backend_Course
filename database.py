import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5435/hw"


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await asyncpg.create_pool(
        os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        min_size=0, max_size=10, timeout=5, command_timeout=5,
    )
    app.state.db_pool = pool
    try:
        yield
    finally:
        await pool.close()


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.db_pool
