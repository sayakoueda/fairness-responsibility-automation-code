"""pytest setup.

Tweak ``sys.path`` so the src/ layout works for tests:
1. Keep the repo root on the path as a safety net (legacy flat-layout
   imports still work).
2. Add ``src/`` so the ``oekaki_behavioural_exp`` package is importable.
3. Import the package once to fire its ``__init__.py`` sys.path hook,
   which is what makes business-code bare imports
   (``import experiment_data`` etc.) resolve afterwards.

In addition, if ``config.yaml`` is missing, copy it from
``config.yaml.example`` for the test run. (Production raises
FileNotFoundError on missing config, but in CI/dev we prioritize a
smooth test experience.)
"""
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"

# Auto-copy config.yaml from the example if missing (test convenience).
_cfg_path = REPO_ROOT / "config.yaml"
_cfg_example_path = REPO_ROOT / "config.yaml.example"
if not _cfg_path.exists() and _cfg_example_path.exists():
    shutil.copy(_cfg_example_path, _cfg_path)

for _p in (REPO_ROOT, SRC_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Trigger the package __init__.py sys.path hook (side effect needed; noqa).
import oekaki_behavioural_exp  # noqa: F401, E402
