from pydantic import BaseModel, Field, NonNegativeInt


class ModelEvaluation(BaseModel):
    id: str
    model_name: str
    model_version: str
    accuracy: float = Field(ge=0, le=1)
    precision: float = Field(ge=0, le=1)
    recall: float = Field(ge=0, le=1)
    f1_score: float = Field(ge=0, le=1)
    dataset_size: NonNegativeInt
    trained_at: str
    notes: str | None = None
