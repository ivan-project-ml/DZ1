
from pydantic import BaseModel, ConfigDict, Field


class Features(BaseModel):
    model_config = ConfigDict(extra = "forbid")
    text: str = Field(
        min_length = 1,
        description = "Text for classification"
    )
class Response(BaseModel):
    label: str = Field(
        title = "Prediction"
    )
    version: str
    request_id: str
    latency_ms: float
