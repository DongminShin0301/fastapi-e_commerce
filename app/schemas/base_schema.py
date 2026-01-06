from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        strict=True,
        extra="forbid",
        from_attributes=True
    )
