"""Run the frozen Phase 5 PPG-DaLiA S14 fault characterization."""

from __future__ import annotations

import argparse
from pathlib import Path

from ml.experiments.ppg_dalia_fault_robustness.experiment import (
    DEFAULT_CONFIG_PATH,
    REPOSITORY_ROOT,
    load_protocol_config,
    run_experiment,
    write_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    config = load_protocol_config(args.config)
    results = run_experiment(REPOSITORY_ROOT, args.config, progress=not args.quiet)
    output_path, report_path = write_artifacts(results, REPOSITORY_ROOT, config)
    print(f"Wrote {output_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
