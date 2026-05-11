"""Characterization test for app_config.TrialConfig.load_config.

Verifies that parsing each task-pattern CSV (solo_a/b, social_c/d)
produces the snapshotted result.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import oekaki_behavioural_exp  # trigger sys.path hook
import trial_config

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "Config"


@pytest.mark.parametrize(
    "name",
    ["solo_a", "solo_b", "social_c", "social_d", "sample_otherself_only"],
)
def test_trial_config_loads(name: str) -> None:
    path = CONFIG_DIR / f"{name}.csv"
    other_or_self, o_or_e_or_d, data_id, durations = trial_config.load_config(
        str(path)
    )
    # All four lists must come back with the same length.
    n = len(other_or_self)
    assert n > 0
    assert len(o_or_e_or_d) == n
    assert len(data_id) == n
    assert len(durations) == n
    # Types: data_id and durations must be int.
    for d in data_id:
        assert isinstance(d, int)
    for d in durations:
        assert isinstance(d, int)


def test_trial_config_solo_a_snapshot() -> None:
    """Lightweight snapshot to make sure solo_a stays untouched."""
    path = CONFIG_DIR / "solo_a.csv"
    other_or_self, o_or_e_or_d, data_id, durations = trial_config.load_config(
        str(path)
    )
    # Header content varies; freeze the actual first-row data instead.
    assert (other_or_self[0], o_or_e_or_d[0], data_id[0], durations[0]) == (
        "other",
        "e",
        1,
        12,
    )


def test_sample_otherself_only_is_all_other() -> None:
    """Sanity check that the otherself-only sample really has every trial as 'other'."""
    path = CONFIG_DIR / "sample_otherself_only.csv"
    other_or_self, o_or_e_or_d, data_id, durations = trial_config.load_config(
        str(path)
    )
    assert all(s == "other" for s in other_or_self)
    assert all(d in ("e", "d") for d in o_or_e_or_d)
    # data_id must be in 1..5 (matching the existing otherself_record_*.csv files).
    assert all(1 <= d <= 5 for d in data_id)
    assert all(isinstance(d, int) and d > 0 for d in durations)


def test_gen_filename_response() -> None:
    import experiment_data

    name = experiment_data.gen_filename(
        experiment_data.FileType.RESPONSE,
        experiment_data.TaskPattern.PATTERN_C,
        experiment_data.Condition.SOCIAL,
        "1234",
    )
    assert name == "social_C_1234_R.csv"


def test_gen_filename_trajectory() -> None:
    import experiment_data

    name = experiment_data.gen_filename(
        experiment_data.FileType.TRAJECTORY,
        experiment_data.TaskPattern.PATTERN_A,
        experiment_data.Condition.SOLO,
        "1234",
        trial_no=0,
    )
    assert name == "solo_A_1_1234_T.csv"
