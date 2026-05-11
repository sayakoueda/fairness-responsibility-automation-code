"""Loader for trial-design CSVs (``Config/{solo,social}_*.csv``).

Split off from the old ``app_config.TrialConfig``. Called from
``experiment_data.OData.set_initial_data`` as
``trial_config.load_config(path)``.

See ``Config/README.md`` for the CSV format.
"""
from __future__ import annotations

import csv
from typing import List, Tuple


def load_config(path: str) -> Tuple[List[str], List[str], List[int], List[int]]:
    """Read a trial-design CSV and return four parallel lists.

    Returns ``(other_or_self, o_or_e_or_d, data_id, durations)``:
    - ``other_or_self``: ``"other"`` or ``"self"``
    - ``o_or_e_or_d``: ``"e"`` or ``"d"`` (per-trial correction kind)
    - ``data_id``: 1-indexed otherself record id (``-1`` for ``self`` trials)
    - ``durations``: per-trial trace length in seconds
    """
    with open(path) as fp:
        total_lines = sum(1 for _ in fp) - 1
        other_or_self: List[str] = [""] * total_lines
        o_or_e_or_d: List[str] = [""] * total_lines
        data_id: List[int] = [-1] * total_lines
        durations: List[int] = [0] * total_lines

        fp.seek(0, 0)
        t = csv.reader(fp)
        next(t)  # skip header row

        for index, row in enumerate(t):
            other_or_self[index] = row[0]
            o_or_e_or_d[index] = row[1]
            data_id[index] = int(row[2]) if row[2].isdigit() else -1
            durations[index] = int(row[3])

    return other_or_self, o_or_e_or_d, data_id, durations
