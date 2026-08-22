from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VideoPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    source_url: str
    provider: str
    embed_url: str
    published_at: datetime | None = None
