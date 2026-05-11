"""Tests for the ``mode`` argument of Trajectory.create_csv.

- mode=None: legacy 5-column schema (otherself-record format, backward
  compat).
- mode='e' (enhanced trial): 9-column schema
  ``[trial_no, frame, raw_x, raw_y, delayed_x, delayed_y,
  enhanced_x, enhanced_y, mouse_state]``. The display position stored
  in ``traj.x``/``traj.y`` is written into ``enhanced_x``/``enhanced_y``;
  ``delayed_x``/``delayed_y`` are left empty. ``raw_x``/``raw_y`` come
  from ``traj.raw_x``/``traj.raw_y`` (or are empty when no raw value
  was provided).
- mode='d' (delayed trial): mirror of mode='e' — ``delayed_x``/``delayed_y``
  are filled, ``enhanced_x``/``enhanced_y`` are left empty.
"""
from __future__ import annotations

import csv
import io

import pytest

import experiment_data


def _make_trajectory(points: list[tuple[float, float, int]]) -> experiment_data.Trajectory:
    """Build a one-trial Trajectory from (x, y, mouse_state) tuples."""
    t = experiment_data.Trajectory()
    for x, y, ms in points:
        t.add_trial(x, y, ms)
    t.sync_set()
    return t


def _make_trajectory_with_raw(
    points: list[tuple[float, float, float, float, int]],
) -> experiment_data.Trajectory:
    """Build a one-trial Trajectory from (x, y, raw_x, raw_y, mouse_state) tuples."""
    t = experiment_data.Trajectory()
    for x, y, rx, ry, ms in points:
        t.add_trial(x, y, ms, raw_x=rx, raw_y=ry)
    t.sync_set()
    return t


SAMPLE_POINTS = [
    # (x, y, mouse_state) - mix points near and far from the circle
    (250.0, 100.0, 1),
    (260.0, 110.0, 1),
    (270.0, 120.0, 0),
    (-50.0, -50.0, 0),  # well outside the circle
]


def _read(data: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data)))


def test_create_csv_default_is_legacy_schema():
    t = _make_trajectory(SAMPLE_POINTS)
    buf = io.StringIO()
    t.create_csv(buf)
    rows = _read(buf.getvalue())
    assert rows[0] == ["trial_no", "frame", "x", "y", "mouse_state"]
    assert len(rows) == 1 + len(SAMPLE_POINTS)
    for i, (x, y, ms) in enumerate(SAMPLE_POINTS):
        assert rows[1 + i][0] == "0"
        assert rows[1 + i][1] == str(i)
        assert float(rows[1 + i][2]) == pytest.approx(x)
        assert float(rows[1 + i][3]) == pytest.approx(y)
        assert rows[1 + i][4] == str(ms)


def test_create_csv_enhanced_mode_fills_only_enhanced_columns():
    t = _make_trajectory(SAMPLE_POINTS)
    buf = io.StringIO()
    t.create_csv(buf, mode="e")
    rows = _read(buf.getvalue())
    assert rows[0] == [
        "trial_no", "frame", "raw_x", "raw_y",
        "delayed_x", "delayed_y",
        "enhanced_x", "enhanced_y",
        "mouse_state",
    ]
    assert len(rows) == 1 + len(SAMPLE_POINTS)
    for i, (x, y, ms) in enumerate(SAMPLE_POINTS):
        r = rows[1 + i]
        # raw_x/y empty because add_trial was called without raw values.
        assert r[2] == ""
        assert r[3] == ""
        # delayed columns left empty for an 'e' trial.
        assert r[4] == ""
        assert r[5] == ""
        # The display position stored in traj.x/y lands in enhanced_x/y.
        assert float(r[6]) == pytest.approx(x)
        assert float(r[7]) == pytest.approx(y)
        assert r[8] == str(ms)


def test_create_csv_delayed_mode_fills_only_delayed_columns():
    t = _make_trajectory(SAMPLE_POINTS)
    buf = io.StringIO()
    t.create_csv(buf, mode="d")
    rows = _read(buf.getvalue())
    assert rows[0] == [
        "trial_no", "frame", "raw_x", "raw_y",
        "delayed_x", "delayed_y",
        "enhanced_x", "enhanced_y",
        "mouse_state",
    ]
    for i, (x, y, _ms) in enumerate(SAMPLE_POINTS):
        r = rows[1 + i]
        # raw_x/y empty because add_trial was called without raw values.
        assert r[2] == ""
        assert r[3] == ""
        # The display position stored in traj.x/y lands in delayed_x/y.
        assert float(r[4]) == pytest.approx(x)
        assert float(r[5]) == pytest.approx(y)
        # enhanced columns left empty for a 'd' trial.
        assert r[6] == ""
        assert r[7] == ""


def test_create_csv_raw_columns_populated_when_provided():
    """When add_trial is given raw_x/raw_y, those values appear in raw_x/raw_y columns."""
    pts = [
        (250.0, 100.0, 248.0, 99.0, 1),
        (260.0, 110.0, 263.0, 108.0, 1),
    ]
    t = _make_trajectory_with_raw(pts)
    buf = io.StringIO()
    t.create_csv(buf, mode="e")
    rows = _read(buf.getvalue())
    for i, (x, y, rx, ry, _ms) in enumerate(pts):
        r = rows[1 + i]
        assert float(r[2]) == pytest.approx(rx)
        assert float(r[3]) == pytest.approx(ry)
        # enhanced columns carry the once-corrected display position.
        assert float(r[6]) == pytest.approx(x)
        assert float(r[7]) == pytest.approx(y)


def test_create_csv_enhanced_and_delayed_carry_same_display_position():
    """Both mode='e' and mode='d' write the stored display position into
    their respective variant column. The trial type is encoded only by
    which pair is populated."""
    pt = [(250.0, 100.0, 1)]
    t_e = _make_trajectory(pt)
    t_d = _make_trajectory(pt)
    buf_e = io.StringIO()
    buf_d = io.StringIO()
    t_e.create_csv(buf_e, mode="e")
    t_d.create_csv(buf_d, mode="d")
    rows_e = _read(buf_e.getvalue())
    rows_d = _read(buf_d.getvalue())
    enh_x, enh_y = float(rows_e[1][6]), float(rows_e[1][7])
    dly_x, dly_y = float(rows_d[1][4]), float(rows_d[1][5])
    # Same source point -> same numbers in the respective variant pair.
    assert (enh_x, enh_y) == (dly_x, dly_y)


def test_create_csv_invalid_mode_raises():
    t = _make_trajectory(SAMPLE_POINTS)
    buf = io.StringIO()
    with pytest.raises(ValueError, match="unsupported mode"):
        t.create_csv(buf, mode="x")
