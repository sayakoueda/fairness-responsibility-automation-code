"""Central registry of project-relative paths.

All paths are derived as absolute paths from the repository root, so
they do not depend on the current working directory. This means
``python -m oekaki_behavioural_exp.launch`` works no matter where it is
invoked from – the same set of resources, configuration and data
directories is always referenced.

The repository root is computed as ``parents[3]`` of this file
(``src/oekaki_behavioural_exp/settings/paths.py`` -> repo root).

Note
----
Some dynamically-built paths such as ``Records/{participant_id}/`` are
still constructed in code as plain string concatenations, on the
assumption that the program is launched with the repository root as
the current working directory. If you ever need to support running
the program from outside the repo, route those paths through this
module too (``scene.py`` / ``experiment_data.py`` write paths in
particular).
"""
from __future__ import annotations

from pathlib import Path

# This file lives at src/oekaki_behavioural_exp/settings/paths.py
PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]

CONFIG_DIR: Path = PROJECT_ROOT / "Config"
RECORDS_DIR: Path = PROJECT_ROOT / "Records"
RESOURCES_DIR: Path = PROJECT_ROOT / "Resources"
OTHERSELF_DIR: Path = RECORDS_DIR / "otherself_records"

CONFIG_PATH: Path = PROJECT_ROOT / "config.yaml"
CONFIG_EXAMPLE_PATH: Path = PROJECT_ROOT / "config.yaml.example"


def resolve(relpath: str) -> str:
    """Resolve a relative path (e.g. ``Resources/...`` from config.yaml)
    against the repository root.

    Returns the original string unchanged if the path is already absolute.
    """
    p = Path(relpath)
    if p.is_absolute():
        return str(p)
    return str(PROJECT_ROOT / p)
