# fairness-responsibility-automation-code
Custom code for a continuous drawing task in a human–automation interaction study.

---

## Requirements

### Original experimental environment

The experiment reported in the manuscript was conducted using Python 3.9 with NumPy 1.21.2, Pygame 2.0.1, python-osc 1.7.7, and SciPy 1.7.1.

### Public release environment

This repository has been organized for public release and tested with the dependency versions listed in `uv.lock`. For a fresh installation, we recommend using the locked environment via `uv`.

- Python 3.9 or later
- pygame 2.5+ / scipy 1.10+ / PyYAML 6.0+

The dependency lock is pinned in `uv.lock`. For pip-based installs
`requirements.txt` / `requirements-dev.txt` are also shipped (generated
via `uv export`, identical to the lock).

## Installation

### System dependencies for pygame

On some Python / OS combinations, especially when using a Python version
for which pygame does not publish wheels yet, pygame is built from source.
In that case, SDL2 development libraries are required.

| OS | Command |
| -- | ------- |
| macOS (Homebrew) | `brew install sdl2 sdl2_ttf sdl2_image sdl2_mixer` |
| Ubuntu / Debian  | `sudo apt-get install libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev libsdl2-mixer-dev` |
| Windows          | Prefer a Python version for which pygame publishes wheels. |

Without these libraries, pygame may install incompletely or fail at runtime;
for example, `pygame.font`, `pygame.image`, or `pygame.mixer` may be unavailable.

After installing the system libraries, rebuild pygame if needed:

```bash
uv cache clean pygame
uv sync --reinstall-package pygame --refresh-package pygame
```

### Using uv (recommended)

If [uv](https://docs.astral.sh/uv/) is installed, you can be ready in
one command:

```bash
cd oekaki_behavioural_exp

uv sync           # main + dev group (pytest)
cp config.yaml.example config.yaml   # initialize the config (required)
```

> If `config.yaml` is missing the program raises `FileNotFoundError`
> at startup. Edit this file to configure your machine's display and
> experiment parameters. At minimum, review the display size
> (`display.width` / `display.height`), frame rate (`system.fps`),
> delay frames (`experiment.delay_frames`), and correction factors
> (`corrector.correction_factor_enhanced` / `correction_factor_adversarial`)
> for your setup. Output goes to `Records/{participant_id}/` and is
> not configurable.

Then run:

```bash
uv run python -m oekaki_behavioural_exp.launch
uv run pytest tests/ -v
```

### Using pip + venv

```bash
git clone <repository-url> oekaki_behavioural_exp
cd oekaki_behavioural_exp

python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # to run tests

cp config.yaml.example config.yaml    # initialize the config (required)
```

## Running

### Launch via dialog (recommended)

```bash
uv run python -m oekaki_behavioural_exp.launch
```

You will be prompted in turn for:

1. **Participant ID**: digits only.
2. **Condition**: `solo` / `social`.
3. **Pattern**: `a`/`b` for solo, `c`/`d` for social.

### Launch from the command line

```bash
uv run python -m oekaki_behavioural_exp.experiment --id 1234 --condition solo --pattern A
uv run python -m oekaki_behavioural_exp.experiment --id 1234 --condition social --pattern C
```

Arguments:

| Arg | Description | Example |
| --- | ----------- | ------- |
| `--id` | Participant id (integer) | `1234` |
| `--condition` | `solo` / `social` | `solo` |
| `--pattern` | `A` / `B` / `C` / `D` (lowercase also accepted) | `A` |


### Instruction images

`Resources/Kyouji/{a,b,c,d}.png` are language-agnostic placeholder
slides shown before each task pattern, and are loaded the same way
regardless of `OEKAKI_LOCALE`. No per-language variants are required.

## Configuring trial design

The trial-by-trial design (which trials are `self` / `other`, which
correction is applied, durations, etc.) is defined by the per-pattern
CSVs in `Config/`. To customize the experiment conditions (change the
trial sequence, swap demo records, or run a custom session), see
[`Config/README.md`](Config/README.md) for the file format, column
reference, and validation tips.

## RMSE side-output

Whenever a trajectory `_T.csv` is written, the experiment also writes
`<basename>_rmse.csv` next to it under `Records/{ID}/`. This file
contains the per-frame on-circle projection, squared error, and the
aggregate RMSE / valid-frame count, in the same column layout as the
bundled standalone tool below. Example:

```
trial_no,frame,x,y,mouse_state,on_circle_x,on_circle_y,error,rmse,valid_data_count
```

`rmse` and `valid_data_count` are populated only on the first data row
(matching the standalone tool's serialization).

## Trajectory CSV schema

The participant trajectory CSVs
(`Records/{ID}/{condition}_{pattern}_{trial}_{ID}_T.csv`) are written
with this 9-column schema:

```
trial_no,frame,raw_x,raw_y,delayed_x,delayed_y,enhanced_x,enhanced_y,mouse_state
```

All coordinates are field-local (origin is the field's top-left corner).

- `raw_x`, `raw_y`: the underlying OS cursor position for that frame.
  Filled on every frame where `SceneTrace` saw a `MOUSEMOTION` event
  (or could fall back to the previous raw position); left empty when
  no raw value was captured.
- `delayed_x`, `delayed_y`: the position the participant actually saw
  drawn on screen — `TracerUI.update`'s once-corrected output, with
  `correction_factor_adversarial = -0.40` and the delay ring buffer
  specified by `experiment.delay_frames` baked in.  **Filled only on
   `d` trials.** Empty on `e` trials.
- `enhanced_x`, `enhanced_y`: the position the participant actually saw
  drawn on screen — `TracerUI.update`'s once-corrected output with
  `correction_factor_enhanced = 0.70` applied. **Filled only on `e`
  trials.** Empty on `d` trials.
- `mouse_state`: mouse-button state (0 = up, 1 = down).

The header is the same regardless of trial type. The trial type itself
is recoverable from which variant pair is populated (or from the
`data` column of `Config/{condition}_{pattern}.csv`).

Pen-up frames and the initial frames of a delayed trial, while the
delay ring buffer specified by `experiment.delay_frames` is still
flushing its sentinel entries, show up in the variant columns at the
sentinel value `(-margin, -margin) ≈
(-224, -224)`. `rmse._is_valid` filters these out via its `< -223`
check.

## Reproducibility policy

- Floating-point details depend on the platform and library versions,
  so we recommend running the lock pinned in `uv.lock`.

## License

MIT License. See [`LICENSE`](LICENSE) for the full text.

`pygame_textinput.py` is Silas Gyger's MIT-licensed work, vendored
into this repository. The original license header is kept intact at
the top of that file.

## Citation

For academic use, see the metadata in [`CITATION.cff`](CITATION.cff).
GitHub's "Cite this repository" button picks it up automatically.

## Known limitations

- The interactive UI (pygame scenes) is not exercised by automated
  tests. Manual smoke testing on the target machine is required.
- This repository does not ship raw participant data.
  `Records/otherself_records/` only contains the demonstration data
  used for reproducibility checks.

## Building otherself records from trial data

`SceneObserve` (the "other-observation" scene) loads one of two
pre-corrected files at runtime, chosen by the trial's e/d flag:

| Trial e/d      | Loaded file                            |
| -------------- | -------------------------------------- |
| `e` (enhanced) | `otherself_record_<n>_enhanced.csv`    |
| `d` (delayed)  | `otherself_record_<n>_delayed.csv`     |

The scene does **not** re-apply the corrector at playback time, so the
contents of these files are exactly the positions that get drawn to
the screen.

To make a new pair, harvest the `enhanced_x` / `enhanced_y` or
`delayed_x` / `delayed_y` columns from a participant's trial
trajectory (`**_T.csv`). Those variant columns already contain the
on-screen positions the original participant saw (the once-corrected
display coordinates that `TracerUI.update` produced). Copy them
verbatim into the otherself record; with the playback path no longer
re-applying the corrector, `SceneObserve` will draw the same pixels
for the next participant. The `raw_x` / `raw_y` columns are for offline
analysis (e.g. computing motor RMSE without correction) — they are
**not** what you want for visual replay.

This is a manual, by-hand workflow — no helper script.

### 1. Pick the source trial

Trial trajectories live under
`Records/<ID>/{condition}_{pattern}_<trial>_<ID>_T.csv`. Open the one
that contains the trial you want to reuse. A single
`otherself_record_<N>_<variant>.csv` holds exactly one trial; pick
one `trial_no` to lift. Note the trial's type (`e` or `d`) — easiest
check: an `e` trial has the `enhanced_x/y` columns populated and
`delayed_x/y` empty; a `d` trial is the mirror. The trial type
decides which columns to read and which output filename suffix to
use.

### 2. Slice the right rows and columns

`**_T.csv` for an `e`/`d` trial uses the 9-column schema:

```
trial_no, frame, raw_x, raw_y, delayed_x, delayed_y, enhanced_x, enhanced_y, mouse_state
   0       1    2      3       4          5          6           7           8
```

The output `otherself_record_<N>_<variant>.csv` uses the 5-column
schema:

```
trial_no, frame, x, y, mouse_state
```

| Source trial `data` | Source x column | Source y column | Output filename                      |
| ------------------- | --------------- | --------------- | ------------------------------------ |
| `e`                 | `enhanced_x` (6) | `enhanced_y` (7) | `otherself_record_<N>_enhanced.csv` |
| `d`                 | `delayed_x` (4)  | `delayed_y` (5)  | `otherself_record_<N>_delayed.csv`  |

Skip the `raw_x` / `raw_y` columns (indices 2, 3) — those reflect the
underlying hand motion before any correction and would produce a
non-corrected playback that doesn't match what the original
participant saw.

### 3. Write the output

Filter to the chosen `trial_no`, then write the rows into
`Records/otherself_records/otherself_record_<N>_<variant>.csv` with:

- `trial_no` reset to `0`
- `frame` re-numbered from `0`
- `x` ← source's `enhanced_x` (or `delayed_x`)
- `y` ← source's `enhanced_y` (or `delayed_y`)
- `mouse_state` copied verbatim

For `d` (delayed) variants, prepend head padding with the same number
of rows as `experiment.delay_frames` so the playback reproduces the
visual delay specified in the original configuration. Each padding row
is `(-1, -1, 0)` — sentinel position with `mouse_state = 0`, which 
makes `SceneObserve` skip drawing for those frames regardless of any
later interpretation of `mouse_state`. Renumber `frame` so the padding
occupies the initial `experiment.delay_frames` rows and the real data
starts immediately after the padding. This matches the `convert.py`
-generated`_delayed.csv` layout.

Example (delayed variant with padding; assuming
`experiment.delay_frames = N`):

trial_no,frame,x,y,mouse_state
0,0,-1,-1,0
0,1,-1,-1,0
...
0,N-1,-1,-1,0
0,N,<source delayed_x>,<source delayed_y>,<source mouse_state>
0,N+1,...
```

Example (enhanced variant — no padding needed):

```
trial_no,frame,x,y,mouse_state
0,0,<source enhanced_x>,<source enhanced_y>,<source mouse_state>
0,1,...
```

Choose `<N>` as the next free index in `Records/otherself_records/`.
The file naming uses the `_enhanced` / `_delayed` suffix directly.

### 4. Mind the pairing

`SceneObserve` picks the loaded file from the trial config: a single
`rec_no` can be referenced from both `e` and `d` trials in
`Config/<condition>_<pattern>.csv`. If so, both
`otherself_record_<N>_enhanced.csv` **and** `otherself_record_<N>_delayed.csv`
must exist. A single self-trial only produces one of the two; to
complete the pair, harvest from a second trial of the opposite type
(an `e` trial for the missing enhanced file, a `d` trial for the
missing delayed file).

### Notes

- **Padding for delayed variants.** The `(-1, -1, 0)` head padding
  should contain the same number of rows as `experiment.delay_frames`,
  reproducing the visual delay specified in the original configuration.
  The `mouse_state = 0` on those rows is what tells
  `SceneObserve` to skip drawing (its `if mouse_state > 0` guard),
  so the position values inside the padding don't matter — any
  off-screen sentinel works.
- **Pen-up frames in the body.** Rows with `mouse_state == 0` inside
  the harvested body (after the padding, if any) are also pen-up
  frames; copy them as-is. `SceneObserve` skips drawing on those.
- **What about `raw_x/y`?** Those columns hold the underlying OS
  cursor position (before `TracerUI`'s correction). They are
  retained for offline analysis — for instance, computing motor RMSE
  uncoupled from the correction factor — but are not suitable as
  otherself record inputs because `SceneObserve` no longer applies
  any correction at playback.

