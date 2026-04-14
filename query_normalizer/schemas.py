from typing import Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Source search query that should be normalized.",
        examples=["Это ghbdtn алфaвиты и машины"],
    )
    debug: Optional[bool] = Field(
        default=False,
        description="If true, includes corrections_applied in response.",
    )


class NormalizationResponse(BaseModel):
    normalized_query: str
    tokens: list[str]
    corrections_applied: list[str]


class BasicNormalizationResponse(BaseModel):
    normalized_query: str
    tokens: list[str]


class AllNormalizationResponse(BaseModel):
    classic: NormalizationResponse
    embedding: NormalizationResponse


class AllBasicNormalizationResponse(BaseModel):
    classic: BasicNormalizationResponse
    embedding: BasicNormalizationResponse
