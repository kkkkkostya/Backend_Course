from repositories.moderation import ModerationRepository
from schemas import Advertisement


class ModerationService:
    def __init__(self, repository: ModerationRepository):
        self.repository = repository

    def predict(self, advertisement: Advertisement) -> bool:
        if advertisement.is_verified_seller:
            return False
        return advertisement.images_qty < self.repository.minimum_images_for_unverified_seller()
