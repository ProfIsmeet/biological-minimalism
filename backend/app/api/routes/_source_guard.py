"""Guards that keep synthetic-only demo logic out of dataset replay."""

from fastapi import HTTPException

from app.engine.data_sources import data_source_manager
from app.schemas.data_source import DataSourceType


def require_synthetic_source(feature: str) -> None:
    if data_source_manager.source_type != DataSourceType.SYNTHETIC:
        raise HTTPException(
            status_code=409,
            detail=f"{feature} is synthetic-demo-only and is unavailable during real dataset replay.",
        )
