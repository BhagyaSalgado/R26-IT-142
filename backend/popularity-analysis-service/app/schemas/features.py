from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt


class TrailerFeatures(BaseModel):
    id: str
    trailer_id: str

    # Raw metrics mapped to the same names used by the Colab notebook.
    views: NonNegativeInt = 0
    likes: NonNegativeInt = 0
    comment_count: NonNegativeInt = 0

    # Engineered features.
    video_age_days: NonNegativeInt
    engagement_rate: NonNegativeFloat
    like_ratio: NonNegativeFloat
    comment_rate: NonNegativeFloat
    comments_per_1000_views: NonNegativeFloat
    views_per_day: NonNegativeFloat
    likes_per_day: NonNegativeFloat = 0
    comments_per_day: NonNegativeFloat = 0
    log_views: NonNegativeFloat = 0
    log_likes: NonNegativeFloat = 0
    log_comments: NonNegativeFloat = 0

    # Existing dashboard/support fields.
    growth_rate: NonNegativeFloat
    popularity_score: NonNegativeFloat = Field(le=100)
    created_at: str
