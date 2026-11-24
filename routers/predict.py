from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from database import get_pool
from repositories.advertisements import AdvertisementRepository
from repositories.moderation import ModerationRepository
from schemas import Advertisement, SimplePredictRequest
from services.moderation import ModerationService

router = APIRouter()


def get_service() -> ModerationService:
    return ModerationService(ModerationRepository())


def get_advertisement_repository(
    connection: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> AdvertisementRepository:
    return AdvertisementRepository(connection)


@router.post("/predict", response_model=bool, responses={
    400: {"description": "Invalid request"},
    500: {"description": "Internal server error"},
})
def predict(advertisement: Advertisement,
            service: Annotated[ModerationService, Depends(get_service)]) -> bool:
    return service.predict(advertisement)


@router.post("/simple_predict", response_model=bool, responses={
    400: {"description": "Invalid request"},
    404: {"description": "Advertisement not found"},
    500: {"description": "Internal server error"},
})
async def simple_predict(
    request: SimplePredictRequest,
    repository: Annotated[AdvertisementRepository, Depends(get_advertisement_repository)],
    service: Annotated[ModerationService, Depends(get_service)],
) -> bool:
    advertisement = await repository.get_for_prediction(request.item_id)
    if advertisement is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return service.predict(advertisement)
