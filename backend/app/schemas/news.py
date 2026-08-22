from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NewsPostListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    excerpt: str
    image_url: str | None = None
    published_at: datetime | None = None


class NewsPostPublic(NewsPostListItem):
    body: str
