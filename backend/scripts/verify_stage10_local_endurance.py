#!/usr/bin/env python3
"""Bounded local Stage 10 S14 multi-client endurance and coherence check."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import time
from pathlib import Path

import httpx
import websockets


def rss_kib(pid: int | None) -> int | None:
    if pid is None:
        return None
    result = subprocess.run(
        ["ps", "-o", "rss=", "-p", str(pid)],
        check=False,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    return int(value) if value.isdigit() else None


async def observe(ws_url: str, origin: str, deadline: float, client_id: int) -> dict[str, object]:
    frames = 0
    predictions = 0
    first_timestamp: float | None = None
    last_timestamp: float | None = None
    last_window = -1
    async with websockets.connect(ws_url, origin=origin, open_timeout=30) as socket:
        while time.monotonic() < deadline:
            frame = json.loads(await asyncio.wait_for(socket.recv(), timeout=10))
            source = frame["source"]
            assert source["source_type"] == "dataset_replay"
            assert source["dataset_name"] == "PPG-DaLiA"
            assert source["subject_id"] == "S14"
            timestamp = float(frame["timestamp"])
            assert last_timestamp is None or timestamp > last_timestamp
            first_timestamp = timestamp if first_timestamp is None else first_timestamp
            last_timestamp = timestamp
            prediction = frame.get("heart_rate_prediction")
            if prediction is not None:
                window = int(prediction["provenance"]["window_index"])
                assert window >= last_window
                last_window = window
                predictions += 1
            frames += 1
    return {
        "client": client_id,
        "frames": frames,
        "predictions": predictions,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "last_window_index": last_window,
    }


async def sample_rss(pid: int | None, deadline: float) -> list[dict[str, int]]:
    samples: list[dict[str, int]] = []
    started = time.monotonic()
    while time.monotonic() < deadline:
        value = rss_kib(pid)
        if value is not None:
            samples.append({"elapsed_seconds": round(time.monotonic() - started), "rss_kib": value})
        await asyncio.sleep(30)
    return samples


async def verify(args: argparse.Namespace) -> dict[str, object]:
    async with httpx.AsyncClient(base_url=args.api_url, timeout=60) as client:
        subjects = (await client.get("/data-source/subjects")).json()
        assert subjects["dataset_name"] == "PPG-DaLiA" and "S14" in subjects["subjects"]
        loaded = (await client.post("/data-source/replay/load", json={"subject_id": "S14"})).json()
        assert loaded["playback_state"] == "paused" and loaded["replay_position_seconds"] == 0
        (await client.post("/data-source/replay/play")).raise_for_status()
        (await client.post("/data-source/replay/speed", json={"speed": 5})).raise_for_status()

    deadline = time.monotonic() + args.duration
    observations, memory = await asyncio.gather(
        asyncio.gather(*(observe(args.ws_url, args.origin, deadline, index) for index in range(args.clients))),
        sample_rss(args.pid, deadline),
    )
    minimum = max(1, int(args.duration * 0.75))
    assert all(item["frames"] >= minimum for item in observations)
    assert all(item["predictions"] > 0 for item in observations)
    last_windows = [int(item["last_window_index"]) for item in observations]
    assert max(last_windows) - min(last_windows) <= 1
    rss_growth = None if len(memory) < 2 else memory[-1]["rss_kib"] - memory[0]["rss_kib"]
    return {
        "result": "PASS",
        "duration_seconds": args.duration,
        "client_count": args.clients,
        "minimum_required_frames_per_client": minimum,
        "clients": observations,
        "multi_client_window_spread": max(last_windows) - min(last_windows),
        "rss_samples": memory,
        "rss_growth_kib": rss_growth,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="http://127.0.0.1:8160")
    parser.add_argument("--ws-url", default="ws://127.0.0.1:8160/ws/live-feed")
    parser.add_argument("--origin", default="http://127.0.0.1:3160")
    parser.add_argument("--duration", type=int, default=600)
    parser.add_argument("--clients", type=int, default=3)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = asyncio.run(verify(args))
    output = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{output}\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
