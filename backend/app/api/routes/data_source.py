"""REST controls for synthetic telemetry and real recorded-data replay."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, HTTPException

from app.data.ppg_dalia import (
    DATASET_NAME,
    PpgDaliaChannelError,
    PpgDaliaPathError,
    PpgDaliaSubjectError,
)
from app.engine.data_sources import (
    ReplayStateError,
    UnsupportedPlaybackSpeedError,
    data_source_manager,
)
from app.schemas.data_source import (
    AvailableSubjectsResponse,
    DataSourceStatus,
    LoadReplayRequest,
    SetPlaybackSpeedRequest,
)

router = APIRouter()


def _controlled(operation: Callable[[], DataSourceStatus]) -> DataSourceStatus:
    try:
        return operation()
    except PpgDaliaSubjectError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PpgDaliaChannelError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PpgDaliaPathError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ReplayStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UnsupportedPlaybackSpeedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/state", response_model=DataSourceStatus, summary="Active telemetry source and replay state")
def get_data_source_state() -> DataSourceStatus:
    return data_source_manager.status()


@router.get("/subjects", response_model=AvailableSubjectsResponse, summary="Available PPG-DaLiA subjects")
def get_available_subjects() -> AvailableSubjectsResponse:
    try:
        subjects = data_source_manager.available_subjects()
    except PpgDaliaPathError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ReplayStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AvailableSubjectsResponse(dataset_name=DATASET_NAME, subjects=subjects)


@router.post("/synthetic", response_model=DataSourceStatus, summary="Use the synthetic demo source")
def select_synthetic_source() -> DataSourceStatus:
    return data_source_manager.use_synthetic()


@router.post("/replay/load", response_model=DataSourceStatus, summary="Load one real PPG-DaLiA subject")
def load_replay(request: LoadReplayRequest) -> DataSourceStatus:
    return _controlled(lambda: data_source_manager.load_replay(request.subject_id, request.channels))


@router.post("/replay/play", response_model=DataSourceStatus, summary="Play or resume dataset replay")
def play_replay() -> DataSourceStatus:
    return _controlled(data_source_manager.play_replay)


@router.post("/replay/pause", response_model=DataSourceStatus, summary="Pause dataset replay")
def pause_replay() -> DataSourceStatus:
    return _controlled(data_source_manager.pause_replay)


@router.post("/replay/reset", response_model=DataSourceStatus, summary="Reset dataset replay to t=0")
def reset_replay() -> DataSourceStatus:
    return _controlled(data_source_manager.reset_replay)


@router.post("/replay/speed", response_model=DataSourceStatus, summary="Set dataset replay speed")
def set_replay_speed(request: SetPlaybackSpeedRequest) -> DataSourceStatus:
    return _controlled(lambda: data_source_manager.set_replay_speed(request.speed))
