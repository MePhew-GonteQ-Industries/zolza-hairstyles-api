from datetime import datetime

from pydantic import field_validator, ConfigDict, BaseModel, Field, UUID4, validator


class CreateService(BaseModel):
    name: str
    min_price: int = Field(gt=0)
    max_price: int = Field(gt=0)
    average_time_minutes: int
    available: bool
    description: str | None = None

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if not v:
            return None

        if len(v) < 60:
            raise ValueError("ensure this value has at least 60 characters")
        elif len(v) > 140:
            raise ValueError("ensure this value has at most 140 characters")
        return v

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("max_price")
    def validate_max_price(cls, v, values):
        if "min_price" in values and v < values["min_price"]:
            raise ValueError(
                "ensure max_price is greater than or equal to the min_price"
            )
        return v

    model_config = ConfigDict(from_attributes=True)


class ReturnService(CreateService):
    required_slots: int
    id: UUID4


class ReturnServiceDetailed(ReturnService):
    # created_by: ReturnUserDetailed TODO: feat-detailed_entity_info
    created_at: datetime
