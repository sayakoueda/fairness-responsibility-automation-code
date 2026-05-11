"""Experiment data model (trial trajectories, questionnaire answers) and file I/O.

This module provides:

- Enums (:class:`Condition`, :class:`TaskPattern`, ...) describing the
  experimental conditions and task patterns.
- :class:`OData`: holds a single session's questionnaire answers.
- :class:`Trajectory`: holds a participant's mouse trajectory data.
- :func:`gen_filename`: builds output CSV file names.

The numerical logic in :meth:`Trajectory.load_csv` and
:meth:`Trajectory._get_correct_pos` is frozen by characterization tests.
Changes to this module should stay within **behavior-preserving** edits
(naming, type annotations, docstrings) only.
"""

from collections import deque
import csv
import enum
from typing import IO, List, Tuple

import app_config
from pygame_constants import *
import corrector
import trial_config

# Short alias to keep references to app_config.experiment concise.
_exp = app_config.experiment


class Condition(enum.Enum):
    """Experimental condition (solo: single-agent / social: dyadic)."""

    SOLO = 0
    SOCIAL = 1
    NONE = -1


class SceneChangeCondition(enum.Enum):
    """Trigger kind that causes a scene transition."""

    TIME = 1
    RIGHT_CLICK = 2
    LEFT_CLICK = 3
    DUMMY = 4
    FLAG = 5


class TaskPattern(enum.Enum):
    """Task pattern (A/B/C/D)."""

    PATTERN_A = 0
    PATTERN_B = 1
    PATTERN_C = 2
    PATTERN_D = 3
    SOLO = 4
    SOCIAL = 5
    NONE = -1


class ColorPattern(enum.Enum):
    """Color pattern (largely unused now, kept for backward compatibility)."""

    PATTERN_P = 0
    PATTERN_Q = 1
    NONE = -1


class AvatarPattern(enum.Enum):
    """Presentation mode for the other participant's avatar."""

    RECORDED = 0
    ENHANCED = 1
    DELAYED = 2
    NONE = 3
    ENHANCED_OR_DELAYED = 4  # umbrella for "anything except RECORDED / NONE"


class EnquetePattern(enum.Enum):
    """Type of questionnaire item."""

    TIME = 0
    SELF = 1
    RESPONSIBILITY = 2


class FileType(enum.Enum):
    """Output file kind (trajectory CSV or response CSV)."""

    TRAJECTORY = 0
    RESPONSE = 1


class PlayModeType(enum.Enum):
    """Playback mode (currently no external references)."""

    none = 0
    enhanced = 1
    delayed = 2


def get_record_data_path(rec_no: int, mode: str | None = None) -> str:
    """Build the path of an otherself record CSV.

    Parameters
    ----------
    rec_no:
        Record index.
    mode:
        When ``"e"`` returns the pre-corrected enhanced variant
        (``otherself_record_<rec_no>_enhanced.csv``); when ``"d"`` returns
        the pre-corrected delayed variant
        (``otherself_record_<rec_no>_delayed.csv``); when ``None`` returns
        the raw record path.
    """
    directory = "Records/otherself_records/"
    filename = "otherself_record_" + str(rec_no)
    if mode == "e":
        filename += "_enhanced"
    elif mode == "d":
        filename += "_delayed"
    elif mode is not None:
        raise ValueError(f"unsupported mode: {mode!r} (expected None / 'e' / 'd')")
    ext = ".csv"
    return directory + filename + ext


def gen_filename(
    filetype: FileType,
    pattern: TaskPattern,
    cond: Condition,
    pid: str,
    trial_no: int = -1,
) -> str:
    """Build the file name for an output CSV.

    Examples: ``solo_A_1_1234_T.csv`` / ``social_C_1234_R.csv``.
    The behavior is frozen by characterization tests; do not change it.
    """
    _sft = "R" if filetype == FileType.RESPONSE else "T"
    _scond = "solo" if cond == Condition.SOLO else "social"
    _sptn = ""
    if pattern == TaskPattern.PATTERN_A:
        _sptn = "A"
    elif pattern == TaskPattern.PATTERN_B:
        _sptn = "B"
    elif pattern == TaskPattern.PATTERN_C:
        _sptn = "C"
    elif pattern == TaskPattern.PATTERN_D:
        _sptn = "D"
    _strial = str(trial_no + 1) if trial_no >= 0 else ""
    _sid = str(pid)
    s = _scond
    if _sptn != "":
        s += "_" + _sptn
    if _strial != "":
        s += "_" + _strial
    s += "_" + _sid + "_" + _sft + ".csv"
    # debug print:
    print(s)
    return s


class OData:
    """Holds a single session's data (participant id, condition, all answers)."""

    def __init__(self) -> None:
        self.patient_id = 0
        self.condition = Condition.NONE
        self.pattern = TaskPattern.NONE
        self.response = {
            "index": 0,
            "other_or_self": None,
            "o_or_e_or_d": None,
            "data_id": None,
            "durations": None,
            "responses": {"R1": [], "R2": [], "R3": []},
        }
        self.trajectory = dict()
        self.current_lines = -1

    def set_initial_data(
        self, id: int, cond: Condition, pat: TaskPattern
    ) -> None:
        """Set the participant id, condition and task pattern, and load
        the matching trial-design CSV.
        """
        self.patient_id = id
        self.condition = cond
        self.pattern = pat
        if self.pattern == TaskPattern.PATTERN_A:
            tmp = trial_config.load_config("Config/solo_a.csv")
        elif self.pattern == TaskPattern.PATTERN_B:
            tmp = trial_config.load_config("Config/solo_b.csv")
        elif self.pattern == TaskPattern.PATTERN_C:
            tmp = trial_config.load_config("Config/social_c.csv")
        elif self.pattern == TaskPattern.PATTERN_D:
            tmp = trial_config.load_config("Config/social_d.csv")
        (
            self.response["other_or_self"],
            self.response["o_or_e_or_d"],
            self.response["data_id"],
            self.response["durations"],
        ) = tmp

    def gen_filename(self, isResponse: bool) -> str:
        """Build the trajectory/response CSV filename based on current state."""
        if isResponse:
            return gen_filename(
                FileType.RESPONSE, self.pattern, self.condition, self.patient_id
            )
        else:
            tn = 0 if self.current_lines == -1 else self.current_lines
            return gen_filename(
                FileType.TRAJECTORY,
                self.pattern,
                self.condition,
                self.patient_id,
                tn,
            )

    def export_csv(self, filepath: str) -> None:
        """Append answers up to the current trial to ``filepath``.

        On the first call (``current_lines == -1``) the header row is written.
        """
        if self.current_lines == -1:
            with open(filepath, 'w', newline="") as fp:
                output = csv.writer(fp)
                header = [
                    "trial",
                    "other_or_self",
                    "enhanced_or_delayed",
                    "data_id",
                    "duration",
                    "R1",
                    "R2",
                    "R3",
                ]
                output.writerow(header)
                self.current_lines += 1
        with open(filepath, 'a', newline="") as fp:
            output = csv.writer(fp)
            _t = self.current_lines
            # debug print:
            print("current_lines", str(_t))
            rows = [
                str(_t),
                self.response["other_or_self"][_t],
                self.response["o_or_e_or_d"][_t],
                self.response["data_id"][_t],
                str(self.response["durations"][_t]),
                str(self.response["responses"]["R1"][_t]),
                str(self.response["responses"]["R2"][_t]),
                str(self.response["responses"]["R3"][_t]),
            ]
            output.writerow(rows)
        self.current_lines += 1

    def format_patient_id(self) -> str:
        """Format the participant id as a zero-padded 6-digit string."""
        return "{:0>6d}".format(self.patient_id)

    # Backward-compatible alias for callers that still use the old name.
    get_patient_id_by_str = format_patient_id

    def add_response(self, ep: EnquetePattern, value) -> None:
        """Append ``value`` as the answer to questionnaire item ``ep``."""
        if ep == EnquetePattern.TIME:
            self.response["responses"]["R1"].append(value)
        elif ep == EnquetePattern.SELF:
            self.response["responses"]["R2"].append(value)
        elif ep == EnquetePattern.RESPONSIBILITY:
            self.response["responses"]["R3"].append(value)


class Trajectory:
    """Container holding one participant's mouse trajectory across many trials.

    ``x`` / ``y`` hold the cursor position the participant actually saw
    drawn on screen (the once-corrected display coordinate that
    ``TracerUI.update`` returned, minus the field margin).
    ``raw_x`` / ``raw_y`` hold the raw OS cursor position in field-local
    coordinates and are populated only when the caller passes them in
    via :meth:`add_trial` (``None`` placeholders for frames where no
    raw value is available).
    """

    def __init__(self) -> None:
        self.frame_max: List[int] = list()  # number of frames per trial
        self.x: List[List[float]] = list()  # display x per trial (once-corrected)
        self.y: List[List[float]] = list()
        self.raw_x: List[List[float | None]] = list()  # raw OS cursor x per trial
        self.raw_y: List[List[float | None]] = list()
        self.mouse_state: List[List[int]] = list()
        # Buffer for the trial currently being recorded.
        self.cs_x: List[float] = list()
        self.cs_y: List[float] = list()
        self.cs_raw_x: List[float | None] = list()
        self.cs_raw_y: List[float | None] = list()
        self.cs_ms: List[int] = list()

    def __len__(self) -> int:
        return len(self.frame_max)

    def append(self, _x: float, _y: float, _m_state: int) -> None:
        """Append one frame to the finalized trial list (auxiliary API,
        not exercised much in current code paths).
        """
        self.x.append(_x)
        self.y.append(_y)
        self.mouse_state.append(_m_state)

    def add_set(
        self,
        _xlist: List[float],
        _ylist: List[float],
        _m_statelist: List[int],
        _raw_xlist: List[float | None] | None = None,
        _raw_ylist: List[float | None] | None = None,
    ) -> None:
        """Append a full trial worth of x/y/mouse_state lists at once.

        When ``_raw_xlist`` / ``_raw_ylist`` are omitted the trial gets a
        list of ``None`` placeholders so downstream code that iterates
        ``raw_x`` / ``raw_y`` still finds matching lengths.
        """
        if len(_xlist) != len(_ylist):
            raise ValueError
        self.x.append(_xlist)
        self.y.append(_ylist)
        self.frame_max.append(len(_ylist))
        self.mouse_state.append(_m_statelist)
        if _raw_xlist is None:
            _raw_xlist = [None] * len(_xlist)
        if _raw_ylist is None:
            _raw_ylist = [None] * len(_ylist)
        self.raw_x.append(_raw_xlist)
        self.raw_y.append(_raw_ylist)

    def add_trial(
        self,
        _x: float,
        _y: float,
        _mouse_st: int,
        raw_x: float | None = None,
        raw_y: float | None = None,
    ) -> None:
        """Append one frame to the buffer of the currently-recording trial.

        ``_x`` / ``_y`` are the once-corrected display coordinates (what
        the participant saw). ``raw_x`` / ``raw_y`` optionally carry the
        underlying raw OS cursor position; pass ``None`` (the default)
        when no raw value is available.
        """
        self.cs_x.append(_x)
        self.cs_y.append(_y)
        self.cs_raw_x.append(raw_x)
        self.cs_raw_y.append(raw_y)
        self.cs_ms.append(_mouse_st)

    def sync_set(self) -> None:
        """Commit the in-progress trial buffer to the trial list and clear it."""
        self.add_set(
            self.cs_x, self.cs_y, self.cs_ms,
            self.cs_raw_x, self.cs_raw_y,
        )
        self.cs_x = []
        self.cs_y = []
        self.cs_raw_x = []
        self.cs_raw_y = []
        self.cs_ms = []

    def clear(self) -> None:
        """Discard all trajectory data."""
        self.x = []
        self.y = []
        self.raw_x = []
        self.raw_y = []
        self.frame_max = []
        self.mouse_state = []
        self.cs_x = []
        self.cs_y = []
        self.cs_raw_x = []
        self.cs_raw_y = []
        self.cs_ms = []

    def create_csv(self, fp: IO[str], mode: str | None = None) -> None:
        """Write the trajectory data as CSV to ``fp``.

        Parameters
        ----------
        fp:
            Text-mode file object to write to.
        mode:
            When ``None``, writes the legacy 5-column schema
            ``[trial_no, frame, x, y, mouse_state]`` using the stored
            display coordinates as ``x``, ``y`` (otherself-record
            format).
            When ``'e'`` (enhanced trial) or ``'d'`` (delayed trial) is
            given, writes the 9-column schema
            ``[trial_no, frame, raw_x, raw_y, delayed_x, delayed_y,
            enhanced_x, enhanced_y, mouse_state]``. ``raw_x`` / ``raw_y``
            come from :attr:`raw_x` / :attr:`raw_y` (the underlying OS
            cursor position; empty when no raw value was provided). The
            once-corrected display coordinates the participant actually
            saw (stored in :attr:`x` / :attr:`y`) are written into the
            variant-matching pair: ``enhanced_x/y`` for ``mode='e'`` and
            ``delayed_x/y`` for ``mode='d'``. The opposite pair is left
            empty so the trial type is recoverable from which columns
            are populated.
        """
        output = csv.writer(fp)
        if mode is None:
            header = ["trial_no", "frame", "x", "y", "mouse_state"]
        elif mode in ("e", "d"):
            header = [
                "trial_no", "frame", "raw_x", "raw_y",
                "delayed_x", "delayed_y",
                "enhanced_x", "enhanced_y",
                "mouse_state",
            ]
        else:
            raise ValueError(f"unsupported mode: {mode!r} (expected None / 'e' / 'd')")
        output.writerow(header)

        for trial_index, fm in enumerate(self.frame_max):
            for i in range(fm):
                x = self.x[trial_index][i]
                y = self.y[trial_index][i]
                ms = self.mouse_state[trial_index][i]
                if mode is None:
                    row = [str(trial_index), str(i), str(x), str(y), str(ms)]
                else:
                    rx = self.raw_x[trial_index][i]
                    ry = self.raw_y[trial_index][i]
                    rx_str = "" if rx is None else str(rx)
                    ry_str = "" if ry is None else str(ry)
                    if mode == "e":
                        row = [
                            str(trial_index), str(i), rx_str, ry_str,
                            "", "", str(x), str(y), str(ms),
                        ]
                    else:  # mode == "d"
                        row = [
                            str(trial_index), str(i), rx_str, ry_str,
                            str(x), str(y), "", "", str(ms),
                        ]
                output.writerow(row)

    def load_csv(
        self,
        filepath: str,
        export_enhanced: bool = False,
        export_delayed: bool = False,
    ) -> None:
        """Load a trajectory from a CSV.

        When ``export_enhanced`` or ``export_delayed`` is true, each
        coordinate pair is transformed through :meth:`_get_correct_pos`
        as it is read in. When ``export_delayed`` is true the output is
        delayed by ``app_config.experiment.delay_frames`` frames via a
        ring buffer.

        This routine is frozen by characterization tests; do not change
        its observable behavior.
        """
        if len(self.frame_max) != 0:
            raise IndexError  # require empty container so writes never overlap
        self.clear()
        with open(filepath) as fp:
            tab = csv.reader(fp)
            next(tab)
            _current_trial = 0
            _previous_trial = 0
            delayed_queue = deque()
            for i in range(0, _exp.delay_frames):
                delayed_queue.append((-1, -1, 0))
            for row in tab:
                # Parse columns:
                # header = ["trial_no", "frame", "x", "y", "mouse_state"]
                _current_trial = int(row[0])
                _x = float(row[2])
                _y = float(row[3])
                _mst = int(row[4])
                if export_enhanced:
                    nx, ny = self._get_correct_pos(_x, _y, is_enhanced=True)
                    _x, _y = nx, ny
                elif export_delayed:
                    nx, ny = self._get_correct_pos(_x, _y, is_delayed=True)
                    delayed_queue.append((nx, ny, _mst))
                    _x, _y, _mst = delayed_queue.popleft()
                if _previous_trial != _current_trial:
                    self.sync_set()
                self.add_trial(_x, _y, _mst)
                _previous_trial = _current_trial
            if export_delayed:
                for _x, _y, _mst in delayed_queue:
                    self.add_trial(_x, _y, _mst)
            self.sync_set()

    def _get_correct_pos(
        self,
        raw_x: float,
        raw_y: float,
        is_delayed: bool = False,
        is_enhanced: bool = False,
    ) -> Tuple[float, float]:
        """Internal helper that turns raw coordinates into corrected ones.

        The actual math lives in :class:`corrector.Corrector`. The
        sequence of calls in this method is frozen by characterization
        tests.
        """
        x, y = corrector.Corrector.get_correct((raw_x, raw_y))
        if is_delayed:
            ex, ey = corrector.Corrector.get_dw_point(
                (raw_x, raw_y),
                (x, y),
                corrector.Corrector.correction_factor_adversarial,
            )
        elif is_enhanced:
            ex, ey = corrector.Corrector.get_dw_point(
                (raw_x, raw_y),
                (x, y),
                corrector.Corrector.correction_factor_enhanced,
            )
        x = x - _exp.margin
        y = y - _exp.margin
        return ex, ey

    def get_pos(
        self, trial_no: int, frame_no: int
    ) -> Tuple[float, float, int, bool, bool]:
        """Return the coordinates and end-of-trial / end-of-trials flags
        for the given trial and frame.

        Returns ``(x, y, mouse_state, is_end_of_trial, is_end_of_trials)``.
        """
        if trial_no >= len(self.frame_max):
            raise IndexError
        if frame_no >= self.frame_max[trial_no]:
            raise IndexError
        _x = self.x[trial_no][frame_no]
        _y = self.y[trial_no][frame_no]
        _mst = self.mouse_state[trial_no][frame_no]
        is_end_of_trial = frame_no + 1 >= self.frame_max[trial_no]
        is_end_of_trials = trial_no + 1 == len(self.frame_max)
        return _x, _y, _mst, is_end_of_trial, is_end_of_trials
