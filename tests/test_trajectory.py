"""Characterization test for experiment_data.Trajectory.load_csv.

Loads an input CSV and verifies that the raw / enhanced / delayed
output CSVs match the golden fixture exactly.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

import experiment_data

REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = REPO_ROOT / "Records" / "otherself_records"
GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden"

NUM_TOL = 1e-9


def _run(record_no: int, mode: str) -> list[list[str]]:
    src = INPUT_DIR / f"otherself_record_{record_no}.csv"
    t = experiment_data.Trajectory()
    t.load_csv(
        str(src),
        export_enhanced=(mode == "enhanced"),
        export_delayed=(mode == "delayed"),
    )
    buf = io.StringIO()
    t.create_csv(buf)
    buf.seek(0)
    return list(csv.reader(buf))


def _read_golden(record_no: int, mode: str) -> list[list[str]]:
    path = GOLDEN_DIR / f"trajectory_record_{record_no}_{mode}.csv"
    with open(path) as fp:
        return list(csv.reader(fp))


def _assert_rows_equal(actual: list[list[str]], expected: list[list[str]]) -> None:
    assert actual[0] == expected[0], "header mismatch"
    assert len(actual) == len(expected), (
        f"row count mismatch: actual={len(actual)} expected={len(expected)}"
    )
    for i, (a, e) in enumerate(zip(actual[1:], expected[1:]), start=1):
        assert len(a) == len(e), f"column count mismatch at row {i}"
        # trial_no, frame, mouse_state are integer strings -> compare with ==
        assert a[0] == e[0], f"trial_no mismatch at row {i}: {a[0]} vs {e[0]}"
        assert a[1] == e[1], f"frame mismatch at row {i}: {a[1]} vs {e[1]}"
        assert a[4] == e[4], f"mouse_state mismatch at row {i}: {a[4]} vs {e[4]}"
        # x, y may be floats; compare with tolerance.
        for col in (2, 3):
            af, ef = float(a[col]), float(e[col])
            assert abs(af - ef) < NUM_TOL, (
                f"col{col} mismatch at row {i}: {af} vs {ef}"
            )


@pytest.mark.parametrize("record_no", [0, 1, 2, 3, 4])
@pytest.mark.parametrize("mode", ["raw", "enhanced", "delayed"])
def test_trajectory_load_matches_golden(record_no: int, mode: str) -> None:
    actual = _run(record_no, mode)
    expected = _read_golden(record_no, mode)
    _assert_rows_equal(actual, expected)
