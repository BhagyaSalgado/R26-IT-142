from pydantic import BaseModel, Field, NonNegativeInt


class TrailerMetrics(BaseModel):
    id: str
    trailer_id: str
    view_count: NonNegativeInt
    like_count: NonNegativeInt
    comment_count: NonNegativeInt
    favorite_count: NonNegativeInt = 0
    collected_at: str
    source: str = Field(default="simulated", description="youtube_api or simulated")


class TrailerMetricsCreate(BaseModel):
    trailer_id: str
    view_count: NonNegativeInt
    like_count: NonNegativeInt
    comment_count: NonNegativeInt
    favorite_count: NonNegativeInt = 0
    source: str = "simulated"
