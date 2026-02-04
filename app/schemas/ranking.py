"""Ranking schemas."""

import uuid
from pydantic import BaseModel


class RankingItem(BaseModel):
    """Item in ranking list."""
    rank: int
    skill_id: uuid.UUID
    slug: str
    name: str
    score: float
    views: int
    stars: int
