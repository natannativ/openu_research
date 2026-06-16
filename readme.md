# ASRT + Mind-Wandering + Visual n-back

A PsychoPy experiment combining an Alternating Serial Reaction Time (ASRT)
implicit-learning task with a concurrent visual n-back load and periodic
thought (mind-wandering) probes. The ASRT design follows
[vekteo/ASRT_jsPsych](https://github.com/vekteo/ASRT_jsPsych) (Vékony, 2021).

All on-screen text is in Hebrew (right-to-left).

## What it measures

- **ASRT**: a white target appears in one of 4 horizontal positions; the
  participant presses the matching key as fast and accurately as possible.
  Positions alternate between a hidden fixed pattern and random locations, so
  implicit learning shows up as faster RTs for high-probability triplets.
- **Visual n-back**: a letter appears in the center each trial. The load
  depends on `condition`:
  - `low_load`  → 0-back: ignore the letter.
  - `high_load` → 1-back: press **SPACE** when the letter matches the previous one.
- **Thought probes**: after each block, 3 short Likert questions about focus,
  thought content, and whether attention drifted spontaneously.
- **Awareness**: one yes/no question at the end about noticing any pattern.

## Requirements

- **Recommended (lab):** install the **Standalone PsychoPy** app —
  https://www.psychopy.org/download.html — and open `main.py` in its Coder view.
- **Alternative (own Python env):** `pip install -r requirements.txt`
  (validated with PsychoPy 2026.1.3, python-bidi 0.6.10).
- macOS ships the `Arial Hebrew` font used for Hebrew glyphs. On other OSes,
  install a comparable Hebrew font or change `HEBREW_FONT` in `main.py`.

## How to run

1. Open `main.py` in PsychoPy Coder (or run `python main.py` in your env).
2. Fill in the start dialog:
   - **participant**: ID. Use a **number** — the ASRT sequence is
     counterbalanced across the 24 possible patterns by participant number, so a
     given number always gets the same sequence (non-numeric IDs get a random
     sequence).
   - **age**, **vision** (normal/corrected).
   - **condition**: `low_load` (0-back) or `high_load` (1-back).
   - **short_version**: tick for a quick pilot run (see below).
   - **fullscreen**: keep on for real data collection.
3. Press the response keys to advance the self-paced screens; press **Escape**
   at any time to quit (data collected so far is saved).

### Response keys

| Position (left → right) | Key |
|---|---|
| outer left  | `S` |
| inner left  | `F` |
| inner right | `J` |
| outer right | `L` |

n-back match = **SPACE** (high_load only).

## Run length

| | Full run | Short version |
|---|---|---|
| Blocks | 25 | 3 |
| Trials per block | 80 | 40 |
| Practice trials | 80 | 20 |
| Approx. duration | ~85 min | ~5–10 min |

Key timing/behaviour parameters live in the `SETTINGS` block at the top of
`main.py` (e.g. `ITI`, `INITIAL_DELAY`, `NBACK_RESPONSE_WINDOW`,
`ASRT_MAX_ATTEMPTS`, `NBACK_WARNING_THRESHOLD`).

## Output files

Written to the working directory; per-trial data is flushed after every block,
so a crash loses at most the current block.

- `data_<participant>_<condition>_<timestamp>.csv` — one row per trial. Key
  columns: `p_or_r` (pattern/random), `asrt_position`, `asrt_correct`,
  `asrt_rt`, `asrt_n_attempts`, `nback_target`, `nback_response`,
  `nback_correct`, `triplet`, `triplet_type` (H/L/R/T/X), `asrt_sequence`, and
  the block's three `probe_*` answers.
- `session_<participant>_<condition>_<timestamp>.csv` — one row per session:
  demographics, `asrt_sequence`, and the end-of-task awareness answer.

## Lab checklist (in-person testing)

- Test on the **actual lab machine** at its real refresh rate.
- Disable notifications, sleep, and auto-updates during a session.
- Use a **wired keyboard** for consistent key timing.
- Pin the PsychoPy version for the whole study; don't upgrade mid-collection.
- Back up the data folder after each participant.
