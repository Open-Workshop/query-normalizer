from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Source search query that should be normalized.",
        examples=["Это ghbdtn алфaвиты и машины"],
    )


class NormalizationResponse(BaseModel):
    original_query: str
    normalized_query: str
    tokens: list[str]
    corrections_applied: list[str]


class AllNormalizationResponse(BaseModel):
    original_query: str
    classic: NormalizationResponse
    embedding: NormalizationResponse
