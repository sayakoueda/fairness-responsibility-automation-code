# Config/ — Trial-design CSV reference

This directory holds the **trial-design CSVs** that describe what
gets shown / drawn in what order, and for how many seconds, in a
single session.

The experiment program loads exactly one of the following files based
on the `--pattern` argument (A / B / C / D). See
`OData.set_initial_data` in
`src/oekaki_behavioural_exp/domain/experiment_data.py` for the wiring:

| `--condition` | `--pattern` | File loaded |
| ------------- | ----------- | ------------------------ |
| `solo`        | `A`         | `Config/solo_a.csv` |
| `solo`        | `B`         | `Config/solo_b.csv` |
| `social`      | `C`         | `Config/social_c.csv` |
| `social`      | `D`         | `Config/social_d.csv` |

The simplest way to run a custom design is to **replace the contents
of the matching file** (or copy your own CSV on top of it). Stash the
original somewhere safe (`git stash`, etc.) before doing so.

---

## File format

A plain header + data rows CSV. **The column order is fixed** (the
column names themselves are not actually consulted by the loader, but
the positional order matters).

```
subj_attrib,data,data_id,duration
other,e,1,12
self,d,,10
other,d,3,13
self,e,,11
...
```

Each row corresponds to **one trial** (one trace period plus three
questionnaire pages). The number of data rows = the number of trials
in one session.

### Column meanings

| Column | Type | Values | Role |
| ------ | ---- | ------ | ---- |
| `subj_attrib` | str | `other` / `self` | Whether the participant **observes** or **draws** in this trial |
| `data` | str | `e` / `d` | Per-trial correction kind (enhanced / delayed) |
| `data_id` | int (or empty) | 1..5 | Demo-record id when `subj_attrib=other`. Leave empty for `self` rows |
| `duration` | int | seconds | Trace-period length for this trial |

#### `subj_attrib`

- **`other`** — The participant only **observes** the playback of
  `Records/otherself_records/otherself_record_{data_id-1}.csv`. Mouse
  input is not recorded (intentionally). For these rows
  **`data_id` is required**.
- **`self`** — The participant traces the circle themselves. The mouse
  trajectory is recorded to `Records/{ID}/..._T.csv`. **`data_id` must
  be empty** for these rows.

#### `data`

| Value | Correction factor (`corrector.py`) | Intuition |
| ----- | ----------------------------------- | --------- |
| `e` | `correction_factor_enhanced = 0.70` | Cursor is **pulled toward** the target circle (looks well-drawn). |
| `d` | `correction_factor_adversarial = -0.40` | Cursor is **pushed away** from the target circle (looks poorly drawn). |

`data` applies in both `self` and `other` trials and uses the same
correction in either case.

In the output CSV (`Records/{ID}/..._T.csv`), only one of
`enhanced_x/y` or `delayed_x/y` is populated for a given row,
matching this `data` value. See "Trajectory CSV schema" in the
top-level README.md for details.

#### `data_id`

A 1-indexed id selecting which
`Records/otherself_records/otherself_record_{N}.csv` to play. The code
maps it to a filename via `int(data_id) - 1` (see
`src/oekaki_behavioural_exp/runtime/scene.py`).

| `data_id` | File |
| --------- | ---- |
| 1 | `otherself_record_0.csv` |
| 2 | `otherself_record_1.csv` |
| 3 | `otherself_record_2.csv` |
| 4 | `otherself_record_3.csv` |
| 5 | `otherself_record_4.csv` |

Leave blank for `subj_attrib=self`. In CSV that is just two consecutive
commas (`,,`); the loader normalizes anything non-decimal to `-1`.

#### `duration`

Trace-period length in seconds, integer. This is independent of the
`experiment.rest_time` / `before_task_time` / `question_time` settings
in `config.yaml`, which control the lengths of the rest / instruction /
questionnaire phases around the trace period.

---

## Validation tips

A few checks to run before kicking off a session:

1. **Header typos.** The loader skips the header line as-is, so a typo
   will not produce a load-time error. Empty / trailing newlines are fine.
2. **`other` rows: `data_id` must be in 1..5** and the corresponding
   `otherself_record_{N-1}.csv` must actually exist under
   `Records/otherself_records/`.
3. **`self` rows: `data_id` must be empty.** Putting a number there does
   no harm but loses meaning.
4. **`data` must be `e` or `d`.** Some code paths fall through to a `d`
   default for unknown values, including capital `E`/`D`; avoid them
   to be safe.
5. **`duration` must be an integer.** A decimal triggers ValueError.
6. **No trailing commas or BOM.** Excel can corrupt files on save;
   sanity-check with `head -3 Config/your_file.csv`.
7. **Trial count.** The code does not enforce a hard upper / lower
   limit, but the existing solo / social designs use 16–32 trials.
   Pick what matches your study.

---

## Sample: otherself-only session

`sample_otherself_only.csv` provides a design where every trial is an
`other` (otherself observation) and there is no `self` drawing. Useful
for replay smoke tests, baseline tasks, and physiology calibration.

```csv
subj_attrib,data,data_id,duration
other,e,1,12
other,d,2,12
other,e,3,12
other,d,4,12
other,e,5,12
other,d,1,12
other,e,2,12
other,d,3,12
other,e,4,12
other,d,5,12
```

To run this sample:

```bash
# 1. Save the original solo_a.csv aside.
cp Config/solo_a.csv Config/solo_a.csv.backup

# 2. Drop the sample into solo_a.csv (the filename is hardwired for pattern A).
cp Config/sample_otherself_only.csv Config/solo_a.csv

# 3. Run with PATTERN_A.
uv run python -m oekaki_behavioural_exp.experiment --id 99001 --condition solo --pattern A

# 4. Restore the original.
mv Config/solo_a.csv.backup Config/solo_a.csv
```

> **Caveat:** `define_taskpattern_social` in `social_c.csv` /
> `social_d.csv` looks up the next row (`index + 1`) for `other` rows,
> so an "all other" design feeds it past the end and crashes with
> IndexError. Run this sample only via `solo_a.csv` / `solo_b.csv`.

The output CSV is `Records/{ID}/solo_A_{n}_{ID}_T.csv`. Because every
trial is `other`, **the mouse trajectory is essentially empty** (no
participant input means x/y do not move). The `enhanced_x/y` /
`delayed_x/y` columns are inert too. Depending on the research goal,
the observation scores in `*_R.csv` (R1 / R2 / R3) may be the more
meaningful target.

---

## Files in this directory

| File | Status | Purpose |
| ---- | ------ | ------- |
| `solo_a.csv` / `solo_b.csv` | **Production** | solo condition (pattern A / B) |
| `social_c.csv` / `social_d.csv` | **Production** | social condition (pattern C / D) |
| `sample_otherself_only.csv` | Sample | "all other" design example |
| `debug.csv` / `_debug.csv` / `_solo_b.csv` | Legacy | Old-format compatibility samples; not referenced by current code; removal candidates |
