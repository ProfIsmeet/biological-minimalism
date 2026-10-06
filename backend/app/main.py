"""FastAPI entrypoint.

Boots the active telemetry source's background tick loop, mounts the REST
routers and the `/ws/live-feed` WebSocket, and configures CORS for the
Next.js frontend. The source defaults to the existing synthetic engine and
can be switched to one real PPG-DaLiA recording.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import urllib.parse
import urllib.request
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import ai_explanation, data_source, digital_twin, metrics, research, sensor_health, simulation
from app.api.websocket import manager
from app.api.websocket import router as ws_router
from app.core.config import settings
from app.engine.data_sources import data_source_manager
from app.ml.inference import create_inference_engine

_tick_task: asyncio.Task | None = None


class _SafeAssetRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never forward a private bootstrap credential to a different host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            old_host = urllib.parse.urlsplit(req.full_url).netloc.lower()
            new_host = urllib.parse.urlsplit(newurl).netloc.lower()
            if old_host != new_host:
                redirected.remove_header("Authorization")
        return redirected

# Resolved once at import time: RuleBasedInferenceEngine unless
# BIOMIN_MODEL_CHECKPOINT_PATH points at a real trained checkpoint (see
# app/ml/inference.py). This never imports torch unless a checkpoint is
# actually configured, so the demo stays torch-free by default.
inference_engine = create_inference_engine()


async def _tick_loop() -> None:
    while True:
        snapshot = data_source_manager.tick(settings.tick_interval_seconds)
        if snapshot is not None:
            await manager.broadcast(snapshot.model_dump(mode="json"))
        await asyncio.sleep(settings.tick_interval_seconds)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _provision_asset(
    path: Path,
    url: str,
    expected_hash: str,
    *,
    max_bytes: int,
) -> None:
    if not url.startswith("https://"):
        raise RuntimeError("Public presentation dataset URL must use HTTPS.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    digest = hashlib.sha256()
    written = 0
    try:
        request_headers = {
            "Accept": "application/octet-stream",
            "User-Agent": "biological-minimalism-deploy/1",
        }
        if settings.presentation_asset_bearer_token:
            request_headers["Authorization"] = f"Bearer {settings.presentation_asset_bearer_token}"
        # GitHub's browser release URL does not accept API bearer tokens for
        # private repositories. Resolve it through the authenticated Releases
        # API, then request the matching asset with the octet-stream media type.
        parsed = urllib.parse.urlsplit(url)
        parts = parsed.path.strip("/").split("/")
        if (
            parsed.netloc.lower() == "github.com"
            and len(parts) >= 6
            and parts[2:4] == ["releases", "download"]
        ):
            owner, repository, tag = parts[0], parts[1], parts[4]
            asset_name = urllib.parse.unquote("/".join(parts[5:]))
            release_url = (
                f"https://api.github.com/repos/{urllib.parse.quote(owner)}/"
                f"{urllib.parse.quote(repository)}/releases/tags/{urllib.parse.quote(tag)}"
            )
            metadata_headers = dict(request_headers)
            metadata_headers["Accept"] = "application/vnd.github+json"
            metadata_request = urllib.request.Request(release_url, headers=metadata_headers)
            opener = urllib.request.build_opener(_SafeAssetRedirectHandler())
            with opener.open(metadata_request, timeout=30) as response:
                release = json.load(response)
            asset = next(
                (item for item in release.get("assets", []) if item.get("name") == asset_name),
                None,
            )
            if asset is None or not str(asset.get("url", "")).startswith("https://api.github.com/"):
                raise RuntimeError("Public presentation asset was not found in the private release.")
            url = str(asset["url"])
        request = urllib.request.Request(url, headers=request_headers)
        opener = urllib.request.build_opener(_SafeAssetRedirectHandler())
        with opener.open(request, timeout=30) as response, temporary.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise RuntimeError("Public presentation asset exceeds the configured size limit.")
                digest.update(chunk)
                target.write(chunk)
        if digest.hexdigest() != expected_hash.lower():
            raise RuntimeError("Downloaded public presentation dataset identity check failed.")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _initialize_public_presentation() -> None:
    """Fail closed before accepting traffic when production assets are wrong."""

    dataset_path = settings.ppg_dalia_path
    expected_hash = settings.presentation_dataset_sha256
    if dataset_path is None:
        raise RuntimeError("Public presentation dataset asset is unavailable.")
    if expected_hash is None or len(expected_hash) != 64:
        raise RuntimeError("Public presentation dataset identity is not configured.")
    if not dataset_path.is_file():
        if settings.presentation_dataset_url is None:
            raise RuntimeError("Public presentation dataset asset is unavailable.")
        _provision_asset(
            dataset_path,
            settings.presentation_dataset_url,
            expected_hash,
            max_bytes=settings.presentation_dataset_max_bytes,
        )
    if _sha256(dataset_path) != expected_hash.lower():
        raise RuntimeError("Public presentation dataset identity check failed.")
    checkpoint_path = settings.ppg_dalia_hr_checkpoint_path
    checkpoint_hash = settings.presentation_checkpoint_sha256.lower()
    if not checkpoint_path.is_file():
        if settings.presentation_checkpoint_url is None:
            raise RuntimeError("Public presentation model asset is unavailable.")
        _provision_asset(
            checkpoint_path,
            settings.presentation_checkpoint_url,
            checkpoint_hash,
            max_bytes=10 * 1024 * 1024,
        )
    if _sha256(checkpoint_path) != checkpoint_hash:
        raise RuntimeError("Public presentation model identity check failed.")
    try:
        data_source_manager.initialize_public_presentation()
    except Exception as exc:
        raise RuntimeError("Public presentation initialization failed.") from exc


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global _tick_task
    if settings.public_presentation_mode:
        try:
            _initialize_public_presentation()
        except Exception:
            # Keep deployment logs free of local paths, signed asset URLs,
            # and nested loader details while still failing closed.
            raise RuntimeError("Public presentation initialization failed.") from None
    _tick_task = asyncio.create_task(_tick_loop())
    try:
        yield
    finally:
        if _tick_task is not None:
            _tick_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await _tick_task


app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="Synthetic-demo and real recorded-dataset replay API for the Biological Minimalism dashboard.",
    lifespan=lifespan,
)

@app.middleware("http")
async def enforce_public_read_only(request: Request, call_next):
    """Block every state-changing public request in presentation mode."""

    origin = request.headers.get("origin")
    if settings.public_presentation_mode and origin and origin not in settings.allowed_origins:
        return JSONResponse(status_code=403, content={"detail": "Origin not allowed."})
    if settings.public_presentation_mode and request.method not in {"GET", "HEAD", "OPTIONS"}:
        return JSONResponse(
            status_code=403,
            content={"detail": "Public presentation is read-only."},
        )
    if settings.public_presentation_mode:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                request_bytes = int(content_length)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length."})
            if request_bytes > settings.public_max_request_bytes:
                return JSONResponse(status_code=413, content={"detail": "Request is too large."})
        try:
            return await asyncio.wait_for(
                call_next(request), timeout=settings.public_request_timeout_seconds
            )
        except TimeoutError:
            return JSONResponse(status_code=504, content={"detail": "Request timed out."})
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(digital_twin.router, tags=["digital-twin"])
app.include_router(sensor_health.router, tags=["sensor-health"])
app.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
app.include_router(data_source.router, prefix="/data-source", tags=["data-source"])
app.include_router(ai_explanation.router, prefix="/ai", tags=["ai"])
app.include_router(research.router, prefix="/research", tags=["research"])
app.include_router(ws_router, tags=["websocket"])


@app.get("/health", tags=["meta"], summary="Liveness check")
def health_check() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.api_version,
        "inference_engine": inference_engine.name,
        "source_type": data_source_manager.source_type.value,
        "public_read_only": settings.public_presentation_mode,
    }
