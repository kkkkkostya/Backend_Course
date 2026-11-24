import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from database import lifespan
from routers.predict import router

app = FastAPI(title="Advertisement moderation API", lifespan=lifespan)
app.include_router(router)
logger = logging.getLogger(__name__)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]})


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    logger.error("Prediction request failed", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
async def root():
    return {"message": "Hello World"}
