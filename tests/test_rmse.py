"""Tests for the in-process RMSE computation.

The implementation is meant to mirror the bundled web tool
(``scripts/csv_processor_cp/src/pages/components/FileUploadForm.tsx``).
These tests pin down the algorithm and the CSV output layout.
"""
from __future__ import annotations

import csv
import io
import math

import pytest

import experiment_data
import rmse


# ------------------------------------------------------------------
# Pure-function tests
# ------------------------------------------------------------------

def _frame(trial: int, fno: int, x: float, y: float, ms: int = 1) -> rmse._Frame:
    return rmse._Frame(trial_no=trial, frame_no=fno, x=x, y=y, mouse_state=ms)


def test_calc_rmse_empty_input_returns_zero_result():
    r = rmse.calc_rmse_by_frame([])
    assert r.rmse == 0.0
    assert r.valid_frames_count == 0
    assert r.error_list == []
    assert r.circle_xy_list == []


def test_point_on_target_circle_has_zero_error_and_zero_rmse():
    """A frame already on the target circle has error 0 and contributes 0 to RMSE."""
    # The web tool's circle is at (244, 244) with radius 244.
    # Pick a point on that circle: angle = 0 -> (244 + 244, 244) = (488, 244).
    on_circle = _frame(0, 0, 488.0, 244.0)
    r = rmse.calc_rmse_by_frame([on_circle])
    assert r.error_list[0] == pytest.approx(0.0)
    assert r.circle_xy_list[0][0] == pytest.approx(488.0)
    assert r.circle_xy_list[0][1] == pytest.approx(244.0)
    assert r.rmse == pytest.approx(0.0)
    assert r.valid_frames_count == 1


def test_point_offset_radially_yields_known_squared_error():
    """A point R+10 along angle 0: target is (488, 244), point is (498, 244),
    squared error should be 100, RMSE = 10.
    """
    pt = _frame(0, 0, 498.0, 244.0)
    r = rmse.calc_rmse_by_frame([pt])
    assert r.error_list[0] == pytest.approx(100.0)
    assert r.rmse == pytest.approx(10.0)
    assert r.valid_frames_count == 1


def test_invalid_filter_excludes_zero_and_far_bottom_left():
    """``isValid`` rejects (≈0,≈0) and (<-223, <-223). Their errors stay in
    ``error_list`` but they do NOT contribute to ``rmse`` /
    ``valid_frames_count``.
    """
    near_zero = _frame(0, 0, 0.0, 0.0)
    far_bl = _frame(0, 1, -224.0, -224.0)
    valid = _frame(0, 2, 498.0, 244.0)  # squared error 100
    r = rmse.calc_rmse_by_frame([near_zero, far_bl, valid])
    assert len(r.error_list) == 3  # all frames contribute to error_list
    assert r.valid_frames_count == 1
    assert r.rmse == pytest.approx(10.0)


def test_rmse_averages_squared_errors_then_takes_sqrt():
    """RMSE = sqrt(mean(squared_errors_of_valid_frames))."""
    # Two valid points, squared errors 100 and 400 -> mean=250 -> sqrt(250)
    pts = [
        _frame(0, 0, 498.0, 244.0),  # err=100 (10 px off, +x direction)
        _frame(0, 1, 244.0, 488.0 + 20.0),  # angle pi/2: target (244, 488); err=400
    ]
    r = rmse.calc_rmse_by_frame(pts)
    assert r.error_list[0] == pytest.approx(100.0)
    assert r.error_list[1] == pytest.approx(400.0)
    assert r.valid_frames_count == 2
    assert r.rmse == pytest.approx(math.sqrt(250.0))


def test_threshold_boundary_minus_223_is_kept():
    """The web-tool filter is strict ``< -223``, so exactly -223 is still valid."""
    f = _frame(0, 0, -223.0, -223.0)
    r = rmse.calc_rmse_by_frame([f])
    assert r.valid_frames_count == 1


def test_threshold_boundary_minus_223p001_is_rejected():
    """Anything more negative than -223 is rejected."""
    f = _frame(0, 0, -223.001, -223.001)
    r = rmse.calc_rmse_by_frame([f])
    assert r.valid_frames_count == 0


# ------------------------------------------------------------------
# Trajectory bridge + CSV layout
# ------------------------------------------------------------------

def _make_trajectory(points):
    t = experiment_data.Trajectory()
    for x, y, ms in points:
        t.add_trial(x, y, ms)
    t.sync_set()
    return t


def test_trajectory_to_frames_flattens_internal_trials():
    t = _make_trajectory([(498.0, 244.0, 1), (244.0, 488.0, 1)])
    frames = rmse.trajectory_to_frames(t)
    assert [(f.trial_no, f.frame_no, f.x, f.y, f.mouse_state) for f in frames] == [
        (0, 0, 498.0, 244.0, 1),
        (0, 1, 244.0, 488.0, 1),
    ]


def test_write_rmse_csv_layout_matches_web_tool():
    """The header and per-row schema match what the web tool writes.

    Notably ``rmse`` and ``valid_data_count`` are populated only on the
    first data row.
    """
    # Frame 0 is on-circle (error 0), frame 1 is off-circle by 10 (error 100).
    t = _make_trajectory([(488.0, 244.0, 1), (244.0, 498.0, 1)])
    buf = io.StringIO()
    result = rmse.write_rmse_csv_from_trajectory(buf, t)
    rows = list(csv.reader(io.StringIO(buf.getvalue())))

    assert rows[0] == [
        "trial_no", "frame", "x", "y", "mouse_state",
        "on_circle_x", "on_circle_y", "error", "rmse", "valid_data_count",
    ]
    # First data row: rmse + valid_data_count populated
    assert rows[1][0] == "0"  # trial_no
    assert rows[1][1] == "0"  # frame
    assert float(rows[1][2]) == pytest.approx(488.0)
    assert float(rows[1][3]) == pytest.approx(244.0)
    assert float(rows[1][7]) == pytest.approx(0.0)  # error column (on-circle)
    assert rows[1][8] != ""
    assert rows[1][9] != ""
    assert float(rows[1][8]) == pytest.approx(result.rmse)
    assert int(rows[1][9]) == result.valid_frames_count

    # Second data row: rmse + valid_data_count empty
    assert rows[2][8] == ""
    assert rows[2][9] == ""
