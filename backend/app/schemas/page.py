from pydantic import BaseModel, ConfigDict


class PagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    title: str
    content: str
