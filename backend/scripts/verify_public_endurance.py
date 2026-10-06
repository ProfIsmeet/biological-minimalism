#!/usr/bin/env python3
"""Bounded multi-client endurance check for the public presentation runtime."""

from __future__ import annotations

import argparse
import asyncio
import json
import time

import httpx
import websockets


async def observe_client(
    ws_url: str,
    origin: str,
    deadline: float,
    client_id: int,
) -> dict[str, object]:
    frames = 0
    first_timestamp: float | None = None
    last_timestamp: float | None = None
    prediction_seen = False
    async with websockets.connect(ws_url, origin=origin, open_timeout=90) as socket:
        while time.monotonic() < deadline:
            frame = json.loads(await asyncio.wait_for(socket.recv(), timeout=10))
            assert frame["source"]["source_type"] == "dataset_replay"
            assert frame["source"]["subject_id"] == "S14"
            timestamp = float(frame["timestamp"])
            first_timestamp = timestamp if first_timestamp is None else first_timestamp
            assert last_timestamp is None or timestamp > last_timestamp
            last_timestamp = timestamp
            prediction_seen = prediction_seen or frame.get("heart_rate_prediction") is not None
            frames += 1
    return {
        "client": client_id,
        "frames": frames,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "prediction_seen": prediction_seen,
    }


async def verify(args: argparse.Namespace) -> None:
    async with httpx.AsyncClient(base_url=args.api_url, timeout=90) as client:
        health = (await client.get("/health", headers={"Origin": args.origin})).json()
        state_response = await client.get("/data-source/state", headers={"Origin": args.origin})
        state_response.raise_for_status()
        state = state_response.json()
        assert health["status"] == "ok"
        assert health["public_read_only"] is True
        assert state["public_read_only"] is True
        assert state["source_type"] == "dataset_replay"
        assert state["subject_id"] == "S14"
        assert state["playback_state"] == "playing"
        rejected = await client.post("/data-source/replay/pause", headers={"Origin": args.origin})
        assert rejected.status_code == 403

    deadline = time.monotonic() + args.duration
    observations = await asyncio.gather(
        *(observe_client(args.ws_url, args.origin, deadline, index) for index in range(args.clients))
    )
    assert all(item["frames"] >= max(1, int(args.duration)) for item in observations)
    assert all(item["prediction_seen"] for item in observations)
    print(json.dumps({"duration_seconds": args.duration, "clients": observations}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--ws-url", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--duration", type=int, default=600)
    parser.add_argument("--clients", type=int, default=3)
    asyncio.run(verify(parser.parse_args()))


if __name__ == "__main__":
    main()
