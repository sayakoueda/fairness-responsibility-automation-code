"""Per-trial RMSE computation, mirroring the bundled web tool.

This module replicates the logic of the standalone CSV processor at
``scripts/csv_processor_cp`` (in particular ``calc_rmse_by_frame`` in
``src/pages/components/FileUploadForm.tsx``) so that the experiment
runtime can emit an ``*_rmse.csv`` next to each trajectory CSV. Feeding
the same _T.csv into the web tool should yield equivalent values.

Notes
-----
- ``RADIUS`` and ``CENTER`` here intentionally match the web tool's
  hard-coded values. They are **not** the same as
  ``corrector.py``'s circle parameters (which use FIELD_SIZE / 2 as
  the center). Keep them in lockstep with the JS source.
- ``valid_data_count`` mirrors the web tool's filter: a frame counts
  as "valid" only when the cursor is neither sitting at the origin
  nor parked at the bottom-left placeholder ``(<-223, <-223)``.
- This module operates on an in-memory ``Trajectory``; it works
  regardless of whether the on-disk CSV uses the legacy 5-column or
  the newer 9-column schema.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from typing import IO, List, Tuple


# Mirrors `RADIUS` / `CENTER` in the web tool. Do not drift from the JS source.
RADIUS: float = 244.0
CENTER_X: float = 244.0
CENTER_Y: float = 244.0


@dataclass(frozen=True)
class _Frame:
    trial_no: int
    frame_no: int
    x: float
    y: float
    mouse_state: int


@dataclass(frozen=True)
class RMSEResult:
    error_list: List[float] = field(default_factory=list)
    circle_xy_list: List[Tuple[float, float]] = field(default_factory=list)
    rmse: float = 0.0
    valid_frames_count: int = 0


def _calc_circle_xy(x: float, y: float) -> Tuple[float, float]:
    """Project (x, y) onto the target circle and return that point.

    Mirrors `calcAngle` + `calcCircleXY` in the web tool (one fused step).
    """
    angle = math.atan2(y - CENTER_Y, x - CENTER_X)
    return (
        CENTER_X + math.cos(angle) * RADIUS,
        CENTER_Y + math.sin(angle) * RADIUS,
    )


def _is_valid(x: float, y: float) -> bool:
    """Web-tool ``isValid``: reject (≈0, ≈0) and (<-223, <-223) placeholders."""
    near_zero = abs(x) < 0.0001 and abs(y) < 0.0001
    far_bottom_left = x < -223 and y < -223
    return not near_zero and not far_bottom_left


def calc_rmse_by_frame(frames: List[_Frame]) -> RMSEResult:
    """Compute per-frame error and an overall RMSE.

    Returns ``RMSEResult`` with parallel ``error_list`` /
    ``circle_xy_list`` (one entry per frame, in the same order as
    ``frames``) and the aggregate ``rmse`` / ``valid_frames_count``.
    Empty input yields an all-zero result without raising.
    """
    if not frames:
        return RMSEResult()

    error_list: List[float] = []
    circle_xy_list: List[Tuple[float, float]] = []
    valid_errors: List[float] = []

    for f in frames:
        cx, cy = _calc_circle_xy(f.x, f.y)
        circle_xy_list.append((cx, cy))
        dx = cx - f.x
        dy = cy - f.y
        sq_err = dx * dx + dy * dy
        error_list.append(sq_err)
        if _is_valid(f.x, f.y):
            valid_errors.append(sq_err)

    rmse = (
        math.sqrt(sum(valid_errors) / len(valid_errors))
        if valid_errors
        else 0.0
    )

    return RMSEResult(
        error_list=error_list,
        circle_xy_list=circle_xy_list,
        rmse=rmse,
        valid_frames_count=len(valid_errors),
    )


def trajectory_to_frames(traj) -> List[_Frame]:
    """Flatten the (trial × frame) structure of a Trajectory into a list of frames."""
    frames: List[_Frame] = []
    for trial_index, fm in enumerate(traj.frame_max):
        for i in range(fm):
            frames.append(_Frame(
                trial_no=trial_index,
                frame_no=i,
                x=traj.x[trial_index][i],
                y=traj.y[trial_index][i],
                mouse_state=traj.mouse_state[trial_index][i],
            ))
    return frames


def write_rmse_csv(
    fp: IO[str], frames: List[_Frame], result: RMSEResult
) -> None:
    """Write the RMSE CSV using the same column layout as the web tool.

    Header: ``trial_no, frame, x, y, mouse_state, on_circle_x,
    on_circle_y, error, rmse, valid_data_count``. The ``rmse`` and
    ``valid_data_count`` columns are populated only on the first data
    row, matching the web tool's serialization.
    """
    writer = csv.writer(fp)
    writer.writerow([
        "trial_no", "frame", "x", "y", "mouse_state",
        "on_circle_x", "on_circle_y", "error", "rmse", "valid_data_count",
    ])
    for i, f in enumerate(frames):
        cx, cy = result.circle_xy_list[i]
        err = result.error_list[i]
        is_first = i == 0
        writer.writerow([
            f.trial_no, f.frame_no, f.x, f.y, f.mouse_state,
            cx, cy, err,
            result.rmse if is_first else "",
            result.valid_frames_count if is_first else "",
        ])


def write_rmse_csv_from_trajectory(fp: IO[str], traj) -> RMSEResult:
    """Convenience: flatten Trajectory, compute RMSE, write the CSV in one call.

    Returns the :class:`RMSEResult` so callers can log or further use it.
    """
    frames = trajectory_to_frames(traj)
    result = calc_rmse_by_frame(frames)
    write_rmse_csv(fp, frames, result)
    return result
