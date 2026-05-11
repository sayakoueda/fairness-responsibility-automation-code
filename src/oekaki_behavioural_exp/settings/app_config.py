"""Single application config loader.

Replaces the old ``settings.json`` + ``params.yaml`` + ``params.py`` trio.
Reads ``config.yaml`` from the repository root and returns it packaged
into dataclasses. If ``config.yaml`` is missing, raises
``FileNotFoundError`` immediately (with a hint to copy from
``config.yaml.example``).

Provides:
- One dataclass per section (``DisplayConfig``, ``SystemConfig``,
  ``TaskConfig``, ``ExperimentConfig``, ``CorrectorConfig``) plus the
  top-level ``AppConfig``.
- Module-level attributes ``display`` / ``system`` / ``task`` /
  ``experiment`` / ``corrector`` for direct access from consumers
  (``app_config.experiment.delay_frames`` etc.).
- ``resolve_font_path()``: maps a comma-separated font candidate list
  to an actual file path on disk. Used by ``pygame_textinput.py``;
  carried over from the old ``app_config.py``.

The trial-design CSV loader (``Config/*.csv``) lives in
``trial_config.py``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import paths


# ------------------------------------------------------------------
# Dataclass definitions
# ------------------------------------------------------------------

@dataclass(frozen=True)
class DisplayConfig:
    width: int = 960
    height: int = 960
    font: str = ""


@dataclass(frozen=True)
class SystemConfig:
    fps: int = 100
    version: int = 220823


@dataclass(frozen=True)
class TaskConfig:
    brush_size: int = 8
    bg_fig_paths: Dict[str, str] = field(default_factory=dict)
    kyouji_imgpaths: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExperimentConfig:
    aug_observer_data_option_01: bool = True
    delay_frames: int = 15
    rest_time: int = 10
    before_task_time: int = 2
    question_time: int = 8
    circle_radius: int = 244
    circle_threshold: int = 150
    circle_width: int = 16
    field_size: int = 512
    window_size: int = 960

    @property
    def margin(self) -> int:
        """Margin between window edge and drawing field, in px.
        Derived from ``window_size`` and ``field_size``.
        """
        return (self.window_size - self.field_size) // 2


@dataclass(frozen=True)
class CorrectorConfig:
    threshold: int = 10201
    correction_factor_enhanced: float = 0.70
    correction_factor_adversarial: float = -0.40


@dataclass(frozen=True)
class AppConfig:
    display: DisplayConfig
    system: SystemConfig
    task: TaskConfig
    experiment: ExperimentConfig
    corrector: CorrectorConfig


# ------------------------------------------------------------------
# Loader
# ------------------------------------------------------------------

def _absolutize_resource_paths(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ``Resources/...`` style relative paths into absolute paths
    rooted at the repository root.
    """
    out = dict(task_data)
    # `brush_path` is intentionally ignored if present in legacy configs;
    # the brush image is no longer loaded at runtime (a plain circle is drawn).
    out.pop("brush_path", None)
    if "bg_fig_paths" in out and isinstance(out["bg_fig_paths"], dict):
        out["bg_fig_paths"] = {
            k: paths.resolve(v) if isinstance(v, str) else v
            for k, v in out["bg_fig_paths"].items()
        }
    if "kyouji_imgpaths" in out and isinstance(out["kyouji_imgpaths"], list):
        out["kyouji_imgpaths"] = [
            paths.resolve(p) if isinstance(p, str) else p for p in out["kyouji_imgpaths"]
        ]
    return out


def load_config(path: Path | str | None = None) -> AppConfig:
    """Load ``config.yaml`` and return an :class:`AppConfig`.

    If ``path`` is omitted, the loader looks at the repository-root
    ``config.yaml``. Raises ``FileNotFoundError`` if it does not exist.
    """
    cfg_path = Path(path) if path is not None else paths.CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"{cfg_path} not found. Copy config.yaml.example to config.yaml and edit it."
        )
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise RuntimeError("PyYAML is required to load config.yaml") from e
    with open(cfg_path, "rt", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"{cfg_path}: top-level must be a YAML mapping")

    return AppConfig(
        display=DisplayConfig(**data.get("display", {})),
        system=SystemConfig(**data.get("system", {})),
        task=TaskConfig(**_absolutize_resource_paths(data.get("task", {}))),
        experiment=ExperimentConfig(**data.get("experiment", {})),
        corrector=CorrectorConfig(**data.get("corrector", {})),
    )


# ------------------------------------------------------------------
# Eagerly load at import time and expose section-level attributes so
# consumers can do ``app_config.experiment.X`` directly.
# ------------------------------------------------------------------

_CFG: AppConfig = load_config()

display: DisplayConfig = _CFG.display
system: SystemConfig = _CFG.system
task: TaskConfig = _CFG.task
experiment: ExperimentConfig = _CFG.experiment
corrector: CorrectorConfig = _CFG.corrector


def get_config() -> AppConfig:
    """Return the :class:`AppConfig` that was loaded at import time."""
    return _CFG


# ------------------------------------------------------------------
# Font path resolution (carried over from the old app_config.py)
# ------------------------------------------------------------------

def resolve_font_path(font_spec: str) -> str | None:
    """Walk a comma-separated list of font names and return the absolute
    path of the first one that resolves on disk.

    ``pygame.font.SysFont`` itself accepts comma-separated lists, but
    ``pygame.font.Font`` (used internally by ``pygame_textinput.py``)
    requires a real file path. This helper bridges the two by resolving
    a path before handing it to ``Font()``.
    """
    import pygame  # type: ignore
    if not pygame.font.get_init():
        pygame.font.init()
    for name in font_spec.split(","):
        name = name.strip()
        if not name:
            continue
        if os.path.isfile(name):
            return name
        p = pygame.font.match_font(name)
        if p:
            return p
    return None
