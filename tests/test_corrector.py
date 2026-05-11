"""Characterization test for the pure functions of Corrector.

The only thing this guarantees is that refactors keep returning
the same values that the golden fixture captured.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import corrector

FIXTURE = Path(__file__).parent / "fixtures" / "golden" / "corrector_grid.json"
TOL = 1e-9


@pytest.fixture(scope="module")
def golden() -> dict:
    with open(FIXTURE) as fp:
        return json.load(fp)


def test_get_correct_grid(golden):
    pts = golden["grid_points"]
    expected = golden["get_correct"]
    for (x, y), (ex, ey) in zip(pts, expected):
        gx, gy = corrector.Corrector.get_correct((x, y))
        assert abs(gx - ex) < TOL
        assert abs(gy - ey) < TOL


def test_get_angle_grid(golden):
    pts = golden["grid_points"]
    expected = golden["get_angle"]
    for (x, y), e in zip(pts, expected):
        a = corrector.Corrector.get_angle((x, y))
        assert abs(a - e) < TOL


def test_norm_angle_grid(golden):
    pts = golden["grid_points"]
    expected = golden["norm_angle"]
    for (x, y), e in zip(pts, expected):
        a = corrector.Corrector.norm_angle(corrector.Corrector.get_angle((x, y)))
        assert abs(a - e) < TOL


def test_distance_to_correct_grid(golden):
    pts = golden["grid_points"]
    expected = golden["get_distance_to_correct"]
    for (x, y), e in zip(pts, expected):
        d = corrector.Corrector.get_distance(
            (x, y), corrector.Corrector.get_correct((x, y))
        )
        assert abs(d - e) < TOL


def test_dw_point_enhanced(golden):
    pts = golden["grid_points"]
    expected = golden["get_dw_point_enhanced"]
    ratio = corrector.Corrector.correction_factor_enhanced
    for (x, y), (ex, ey) in zip(pts, expected):
        gx, gy = corrector.Corrector.get_dw_point(
            (x, y), corrector.Corrector.get_correct((x, y)), ratio
        )
        assert abs(gx - ex) < TOL
        assert abs(gy - ey) < TOL


def test_dw_point_adversarial(golden):
    pts = golden["grid_points"]
    expected = golden["get_dw_point_adversarial"]
    ratio = corrector.Corrector.correction_factor_adversarial
    for (x, y), (ex, ey) in zip(pts, expected):
        gx, gy = corrector.Corrector.get_dw_point(
            (x, y), corrector.Corrector.get_correct((x, y)), ratio
        )
        assert abs(gx - ex) < TOL
        assert abs(gy - ey) < TOL
