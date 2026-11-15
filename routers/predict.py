from typing import Annotated

from fastapi import APIRouter, Depends

from repositories.moderation import ModerationRepository
from schemas import Advertisement
from services.moderation import ModerationService

router = APIRouter()


def get_service() -> ModerationService:
    return ModerationService(ModerationRepository())


@router.post("/predict", response_model=bool, responses={
    400: {"description": "Invalid request"},
    500: {"description": "Internal server error"},
})
def predict(advertisement: Advertisement,
            service: Annotated[ModerationService, Depends(get_service)]) -> bool:
    return service.predict(advertisement)
