from dataclasses import asdict

from fastapi import FastAPI

from app.normalization import QueryNormalizer
from app.schemas import AllNormalizationResponse, NormalizationResponse, QueryRequest


app = FastAPI(
    title="Query Normalizer",
    description="FastAPI microservice for search-query normalization.",
    version="0.1.0",
)

normalizer = QueryNormalizer()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/for/classic", response_model=NormalizationResponse)
def normalize_for_classic(payload: QueryRequest) -> NormalizationResponse:
    result = normalizer.normalize_for_classic(payload.query)
    return NormalizationResponse(**asdict(result))


@app.post("/for/embedding", response_model=NormalizationResponse)
def normalize_for_embedding(payload: QueryRequest) -> NormalizationResponse:
    result = normalizer.normalize_for_embedding(payload.query)
    return NormalizationResponse(**asdict(result))


@app.post("/for/all", response_model=AllNormalizationResponse)
def normalize_for_all(payload: QueryRequest) -> AllNormalizationResponse:
    classic = normalizer.normalize_for_classic(payload.query)
    embedding = normalizer.normalize_for_embedding(payload.query)

    return AllNormalizationResponse(
        original_query=payload.query,
        classic=NormalizationResponse(**asdict(classic)),
        embedding=NormalizationResponse(**asdict(embedding)),
    )
