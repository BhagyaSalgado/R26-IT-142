from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt


class TrailerFeatures(BaseModel):
    id: str
    trailer_id: str
    video_age_days: NonNegativeInt
    engagement_rate: NonNegativeFloat
    like_ratio: NonNegativeFloat
    comment_rate: NonNegativeFloat
    comments_per_1000_views: NonNegativeFloat
    views_per_day: NonNegativeFloat
    growth_rate: NonNegativeFloat
    popularity_score: NonNegativeFloat = Field(le=100)
    created_at: str
