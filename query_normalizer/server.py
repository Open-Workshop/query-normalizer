"""FastAPI server for query normalization."""

from typing import Union
from dataclasses import asdict

from fastapi import FastAPI

from query_normalizer.core import QueryNormalizer
from query_normalizer.schemas import (
    AllBasicNormalizationResponse,
    AllNormalizationResponse,
    BasicNormalizationResponse,
    NormalizationResponse,
    QueryRequest,
)

app = FastAPI(
    title="Query Normalizer",
    description="API for search-query normalization.",
    version="0.1.0",
)

normalizer = QueryNormalizer()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/normalize/classic", response_model=Union[NormalizationResponse, BasicNormalizationResponse]
)
def normalize_for_classic(
    payload: QueryRequest,
) -> Union[NormalizationResponse, BasicNormalizationResponse]:
    result = normalizer.normalize_for_classic(payload.query)
    if payload.debug:
        return NormalizationResponse(**asdict(result))
    return BasicNormalizationResponse(
        normalized_query=result.normalized_query,
        tokens=result.tokens,
    )


@app.post(
    "/normalize/embedding", response_model=Union[NormalizationResponse, BasicNormalizationResponse]
)
def normalize_for_embedding(
    payload: QueryRequest,
) -> Union[NormalizationResponse, BasicNormalizationResponse]:
    result = normalizer.normalize_for_embedding(payload.query)
    if payload.debug:
        return NormalizationResponse(**asdict(result))
    return BasicNormalizationResponse(
        normalized_query=result.normalized_query,
        tokens=result.tokens,
    )


@app.post(
    "/normalize", response_model=Union[AllNormalizationResponse, AllBasicNormalizationResponse]
)
def normalize_for_all(
    payload: QueryRequest,
) -> Union[AllNormalizationResponse, AllBasicNormalizationResponse]:
    classic = normalizer.normalize_for_classic(payload.query)
    embedding = normalizer.normalize_for_embedding(payload.query)

    if payload.debug:
        return AllNormalizationResponse(
            classic=NormalizationResponse(**asdict(classic)),
            embedding=NormalizationResponse(**asdict(embedding)),
        )
    return AllBasicNormalizationResponse(
        classic=BasicNormalizationResponse(
            normalized_query=classic.normalized_query,
            tokens=classic.tokens,
        ),
        embedding=BasicNormalizationResponse(
            normalized_query=embedding.normalized_query,
            tokens=embedding.tokens,
        ),
    )
