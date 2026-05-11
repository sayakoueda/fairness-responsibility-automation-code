"""``oekaki_behavioural_exp`` package.

To keep flat-style bare imports working after the move into a packaged
``src/`` layout (``import scene``, ``from pygame_constants import *``,
``import pygame_textinput`` etc.), this ``__init__.py`` injects the
package directory and every sub-package into ``sys.path``.

Thanks to that hook, business code in this package keeps working even
after files were relocated into ``settings/``, ``domain/`` and
``runtime/``: only the renamed module names need to follow.

If external code imports submodules with the package-qualified form
(``from oekaki_behavioural_exp import scene``) it may end up loading
the same module twice (once bare, once qualified). This package is
**not intended to be used as a library**; it is a collection of
experiment scripts and is meant to be executed directly via
``python -m oekaki_behavioural_exp.<entrypoint>``.
"""
import sys as _sys
from pathlib import Path as _Path

_pkg_dir = _Path(__file__).resolve().parent


def _insert(path: _Path) -> None:
    p = str(path)
    if p not in _sys.path:
        _sys.path.insert(0, p)


# Package directory itself, so flat top-level entrypoints (``launch.py``
# etc.) can still bare-import sibling modules.
_insert(_pkg_dir)
# Third-party vendored libraries.
_insert(_pkg_dir / "vendor")
# Role-based sub-packages: settings / domain / runtime.
for _sub in ("settings", "domain", "runtime"):
    _candidate = _pkg_dir / _sub
    if _candidate.is_dir():
        _insert(_candidate)
