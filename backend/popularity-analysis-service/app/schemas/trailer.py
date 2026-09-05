from pydantic import BaseModel, Field


class Trailer(BaseModel):
    id: str
    youtube_video_id: str
    youtube_url: str
    title: str
    channel_name: str
    published_at: str
    thumbnail_url: str | None = None
    created_at: str
    updated_at: str


class TrailerCreate(BaseModel):
    youtube_video_id: str
    youtube_url: str
    title: str
    channel_name: str
    published_at: str
    thumbnail_url: str | None = None


class TrailerLookupResponse(BaseModel):
    trailer: Trailer
