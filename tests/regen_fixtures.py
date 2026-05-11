"""Regenerate the golden fixtures.

Run the current code as-is and freeze its output as the new fixture.
**Do not run this routinely.** Only run it on purpose when you want to
update the baseline.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import sys
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import experiment_data  # noqa: E402
import corrector  # noqa: E402

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "golden"
INPUT_DIR = REPO_ROOT / "Records" / "otherself_records"


def regen_trajectory_fixtures() -> None:
    """Convert otherself_record_0..4 in raw / enhanced / delayed mode and
    freeze the output CSVs as fixtures.
    """
    for rec_no in range(5):
        src = INPUT_DIR / f"otherself_record_{rec_no}.csv"
        if not src.exists():
            print(f"skip: {src}")
            continue
        for mode in ("raw", "enhanced", "delayed"):
            t = experiment_data.Trajectory()
            t.load_csv(
                str(src),
                export_enhanced=(mode == "enhanced"),
                export_delayed=(mode == "delayed"),
            )
            out = FIXTURE_DIR / f"trajectory_record_{rec_no}_{mode}.csv"
            with open(out, "w", newline="") as fp:
                t.create_csv(fp)
            print(f"wrote: {out}")


def regen_corrector_fixtures() -> None:
    """Evaluate the pure functions of Corrector on a grid of points and
    freeze the results as JSON.
    """
    out: dict[str, list] = {}
    grid_pts = [
        (x, y)
        for x in range(0, 513, 32)
        for y in range(0, 513, 32)
    ]
    out["get_correct"] = [
        list(corrector.Corrector.get_correct(p)) for p in grid_pts
    ]
    out["get_angle"] = [corrector.Corrector.get_angle(p) for p in grid_pts]
    out["norm_angle"] = [
        corrector.Corrector.norm_angle(corrector.Corrector.get_angle(p))
        for p in grid_pts
    ]
    out["get_distance_to_correct"] = [
        corrector.Corrector.get_distance(p, corrector.Corrector.get_correct(p))
        for p in grid_pts
    ]
    out["get_dw_point_enhanced"] = [
        list(
            corrector.Corrector.get_dw_point(
                p,
                corrector.Corrector.get_correct(p),
                corrector.Corrector.correction_factor_enhanced,
            )
        )
        for p in grid_pts
    ]
    out["get_dw_point_adversarial"] = [
        list(
            corrector.Corrector.get_dw_point(
                p,
                corrector.Corrector.get_correct(p),
                corrector.Corrector.correction_factor_adversarial,
            )
        )
        for p in grid_pts
    ]
    out["grid_points"] = [list(p) for p in grid_pts]
    out_path = FIXTURE_DIR / "corrector_grid.json"
    with open(out_path, "w") as fp:
        json.dump(out, fp, indent=2)
    print(f"wrote: {out_path}")


if __name__ == "__main__":
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    regen_trajectory_fixtures()
    regen_corrector_fixtures()
    print("done")
