from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

PositiveInt = Annotated[int, Field(strict=True, gt=0)]
NonEmptyString = Annotated[str, Field(strict=True, min_length=1)]


class Advertisement(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", str_strip_whitespace=True)

    seller_id: PositiveInt
    is_verified_seller: bool
    item_id: PositiveInt
    name: NonEmptyString
    description: NonEmptyString
    category: PositiveInt
    images_qty: Annotated[int, Field(strict=True, ge=0)]
