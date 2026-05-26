# -*- coding: utf-8 -*-
from psychopy import visual, core, gui, data, event
from psychopy.hardware import keyboard
from bidi.algorithm import get_display
import random
import csv
import os

def rtl(text):
    # PsychoPy's TextStim renders characters in logical order. Hebrew needs
    # the bidi algorithm applied per-line so RTL display is correct while
    # multi-line layout is preserved.
    return "\n".join(get_display(line) for line in text.split("\n"))

# macOS ships Arial Hebrew with proper Hebrew glyph metrics; the default Arial
# kerns Hebrew unevenly because it isn't tuned for the script.
HEBREW_FONT = "Arial Hebrew"

# =========================
# SETTINGS
# =========================
# NOTE: 25 blocks * 80 trials = 2000 trials ~ 85 min before probes. Adjust if needed.
N_BLOCKS = 25
TRIALS_PER_BLOCK = 80          # 10 repetitions of 8-item ASRT cycle
N_PRACTICE_TRIALS = 24         # random-position familiarization, not saved to CSV
FIXATION_TIME = 0.3
STIM_TIMEOUT = 2.0
ITI = 0.12
PROBE_SCALE = ["1", "2", "3", "4"]

# ASRT pattern: 4 fixed positions, cycled 10 times per block.
# Block layout follows vekteo/ASRT_jsPsych: a random "lead-in" at trial 1
# (preceded by INITIAL_DELAY), then alternating pattern/random from trial 2
# onwards, ending on a pattern at trial 80. So patterns sit at trial numbers
# 2, 4, 6, ..., 80 and randoms at 1, 3, 5, ..., 79.
ASRT_PATTERN = [2, 4, 3, 1]
INITIAL_DELAY = 1.0            # blank delay (seconds) before the first stim of each block
SHOW_BLOCK_FEEDBACK = True     # 5-second accuracy/RT screen after each block

# Key mapping for ASRT positions
POS_KEYS = {
    1: "s",
    2: "f",
    3: "j",
    4: "l"
}

# Visual positions for the 4 locations
POS_COORDS = {
    1: (-0.45, 0.0),
    2: (-0.15, 0.0),
    3: (0.15, 0.0),
    4: (0.45, 0.0)
}

# n-back stimuli
NBACK_STIMULI = ["A", "B", "C", "D", "E", "F"]
NBACK_TARGET_RATE = 0.25       # injected target rate on eligible trials (after the n_back_level lead-in)

# =========================
# PARTICIPANT INFO
# =========================
info = {
    "participant": "",
    "age": "",
    "vision": ["normal", "corrected"],
    "condition": ["low_load", "high_load"],   # low = 1-back, high = 2-back
    "fullscreen": True
}

dlg = gui.DlgFromDict(info, title="ASRT + Mind Wandering + Visual n-back")
if not dlg.OK:
    core.quit()

participant = info["participant"]
age = info["age"]
vision = info["vision"]
condition = info["condition"]
fullscreen = info["fullscreen"]

n_back_level = 1 if condition == "low_load" else 2

# =========================
# DATA FILE
# =========================
timestamp = data.getDateStr()
filename = f"data_{participant}_{condition}_{timestamp}.csv"
out_path = os.path.join(os.getcwd(), filename)

fieldnames = [
    "participant", "condition", "n_back_level",
    "block", "trial_in_block", "global_trial",
    "p_or_r",  # "P" pattern / "R" random, matches vekteo
    "asrt_position", "asrt_correct_key", "asrt_response", "asrt_correct", "asrt_rt",
    "nback_letter", "nback_target", "nback_response", "nback_correct",
    "triplet", "triplet_type",
    "probe_focus", "probe_content", "probe_spontaneous"
]
# awareness is collected once per session and written to a sidecar file
session_filename = f"session_{participant}_{condition}_{timestamp}.csv"
session_path = os.path.join(os.getcwd(), session_filename)

# =========================
# WINDOW AND STIMULI
# =========================
win = visual.Window(
    size=[1400, 900],
    fullscr=fullscreen,
    color="black",
    units="height"
)

kb = keyboard.Keyboard()

fixation = visual.TextStim(win, text="+", color="white", height=0.05)
target_stim = visual.Circle(win, radius=0.025, fillColor="white", lineColor="white")
nback_text = visual.TextStim(win, text="", pos=(0, 0.18), color="white", height=0.05)

instructions = visual.TextStim(
    win,
    text=rtl(
        "ברוך/ה הבא/ה לניסוי.\n\n"
        "בכל ניסיון יופיע עיגול לבן באחד מ-4 מיקומים על המסך.\n"
        "יש ללחוץ מהר ובדיוק על המקש המתאים:\n\n"
        "S = שמאל חיצוני\n"
        "F = שמאל פנימי\n"
        "J = ימין פנימי\n"
        "L = ימין חיצוני\n\n"
        "בנוסף, תופיע במרכז המסך אות.\n"
        f"בתנאי זה עליך לזהות האם האות הנוכחית זהה לאות שהופיעה לפני {n_back_level} צעדים.\n"
        "אם כן, יש ללחוץ על רווח.\n\n"
        "אחרי כל בלוק תופיע/נה שאלה/שאלות קצרות.\n\n"
        "לחצ/י SPACE כדי להתחיל."
    ),
    color="white",
    height=0.035,
    wrapWidth=1.2,
    font=HEBREW_FONT
)

probe_text = visual.TextStim(win, text="", color="white", height=0.04, wrapWidth=1.2, font=HEBREW_FONT)
end_text = visual.TextStim(
    win,
    text=rtl(
        "תודה רבה על השתתפותך!\n\n"
        "תיאור קצר של המחקר:\n"
        "במטלה היה דפוס נסתר במיקומי העיגול — לסירוגין, מיקום קבוע (לפי הסדר 2→4→3→1) ומיקום אקראי. "
        "אנו בודקים האם אנשים לומדים דפוסים סטטיסטיים כאלה ללא מודעות, וכיצד עומס קוגניטיבי (n-back) משפיע על למידה זו.\n\n"
        "אם יש לך שאלות לגבי המחקר, ניתן לפנות לחוקרים.\n\n"
        "לחצ/י SPACE לסיום."
    ),
    color="white",
    height=0.035,
    wrapWidth=1.5,
    font=HEBREW_FONT
)

awareness_question = visual.TextStim(
    win,
    text=rtl(
        "האם הבחנת בדפוס או חוקיות כלשהם במהלך המטלה?\n\n"
        "Y = כן\nN = לא"
    ),
    color="white",
    height=0.045,
    wrapWidth=1.2,
    font=HEBREW_FONT
)

practice_instructions = visual.TextStim(
    win,
    text=rtl(
        "לפני המטלה האמיתית — בלוק תרגול קצר.\n\n"
        "עיגול יופיע באחד מ-4 מיקומים. לחצ/י S / F / J / L.\n"
        "במרכז תופיע אות; אם היא זהה לאות מלפני N צעדים — לחצ/י רווח.\n\n"
        "התרגול אינו נשמר. לחצ/י SPACE להתחיל."
    ),
    color="white",
    height=0.035,
    wrapWidth=1.2,
    font=HEBREW_FONT
)

practice_done_text = visual.TextStim(
    win,
    text=rtl("התרגול הסתיים.\n\nלחצ/י SPACE להתחלת המטלה האמיתית."),
    color="white",
    height=0.04,
    wrapWidth=1.2,
    font=HEBREW_FONT
)

# Between-block rest screen; text is set per-block before drawing.
break_text = visual.TextStim(
    win,
    text="",
    color="white",
    height=0.04,
    wrapWidth=1.2,
    font=HEBREW_FONT
)

# Per-block feedback (accuracy + mean RT). Text set per-block before drawing.
feedback_text = visual.TextStim(
    win,
    text="",
    color="white",
    height=0.04,
    wrapWidth=1.4,
    font=HEBREW_FONT
)

# =========================
# HELPERS
# =========================
def draw_trial(position, letter):
    target_stim.pos = POS_COORDS[position]
    nback_text.text = letter
    target_stim.draw()
    nback_text.draw()

def get_asrt_sequence_for_block():
    """Build an 80-trial ASRT block matching vekteo/ASRT_jsPsych:

      trial 1     : random lead-in
      trial 2     : pattern element 0 (= 2)
      trial 3     : random
      trial 4     : pattern element 1 (= 4)
      ...
      trial 80    : pattern element 3 (= 1, last of the 10th cycle)

    Pattern slots at even trial numbers (2,4,...,80) — 40 patterns total.
    Random slots at odd trial numbers (1,3,...,79) — 40 randoms total.
    """
    seq = [random.choice([1, 2, 3, 4])]  # trial 1: random lead-in
    for rep in range(10):
        for sp in range(4):
            seq.append(ASRT_PATTERN[sp])              # pattern at even trial
            if not (rep == 9 and sp == 3):            # no trailing random after last pattern
                seq.append(random.choice([1, 2, 3, 4]))  # random at next odd trial
    return seq

def get_nback_sequence(length, n_back):
    """Generate an n-back letter sequence with a calibrated target rate.

    First `n_back` letters are random (no valid n-back history yet). For each
    subsequent position, with probability NBACK_TARGET_RATE the letter is set
    equal to seq[i - n_back] (injected target); otherwise it is sampled from
    the 5 letters that are NOT equal to seq[i - n_back], guaranteeing a
    non-target. Resulting target rate on eligible trials is exactly NBACK_TARGET_RATE.
    """
    seq = []
    for i in range(length):
        if i < n_back:
            seq.append(random.choice(NBACK_STIMULI))
            continue
        ref = seq[i - n_back]
        if random.random() < NBACK_TARGET_RATE:
            seq.append(ref)
        else:
            non_targets = [s for s in NBACK_STIMULI if s != ref]
            seq.append(random.choice(non_targets))
    return seq

def build_high_triplets():
    # From pattern: 2-X-4, 4-X-3, 3-X-1, 1-X-2
    high = set()
    bases = [(2, 4), (4, 3), (3, 1), (1, 2)]
    for first, third in bases:
        for middle in [1, 2, 3, 4]:
            high.add((first, middle, third))
    return high

HIGH_TRIPLETS = build_high_triplets()

def classify_triplet(prev2, prev1, current):
    # Labels follow vekteo/ASRT_jsPsych (dataUpdate.js): H high, L low,
    # R repetition (X-X-X), T trill (X-Y-X with X!=Y), X exclude (no triplet
    # history yet). Order matters: high is checked first. R and T are
    # mutually exclusive with each other and (by ASRT construction) cannot
    # overlap with H, but the explicit order documents the convention.
    if prev2 is None or prev1 is None:
        return "", "X"
    tri = (prev2, prev1, current)
    tri_str = f"{tri[0]}-{tri[1]}-{tri[2]}"
    if tri in HIGH_TRIPLETS:
        tri_type = "H"
    elif tri[0] == tri[1] == tri[2]:
        tri_type = "R"
    elif tri[0] == tri[2] and tri[0] != tri[1]:
        tri_type = "T"
    else:
        tri_type = "L"
    return tri_str, tri_type

def quit_experiment():
    try:
        csv_file.close()
    except Exception:
        pass
    win.close()
    core.quit()

def run_probe(question_text, allowed_keys):
    kb.clearEvents()
    probe_text.text = question_text
    listen_keys = list(allowed_keys) + ["escape"]
    while True:
        probe_text.draw()
        win.flip()
        keys = kb.getKeys(keyList=listen_keys, waitRelease=False)
        if keys:
            if keys[0].name == "escape":
                quit_experiment()
            return keys[0].name

def wait_for_space():
    kb.clearEvents()
    while True:
        keys = kb.getKeys(keyList=["space", "escape"], waitRelease=False)
        if keys:
            if keys[0].name == "escape":
                quit_experiment()
            return

# =========================
# START
# =========================
instructions.draw()
win.flip()
wait_for_space()

# =========================
# PRACTICE BLOCK (random positions, NOT saved)
# =========================
practice_instructions.draw()
win.flip()
wait_for_space()

practice_positions = [random.choice([1, 2, 3, 4]) for _ in range(N_PRACTICE_TRIALS)]
practice_nback = get_nback_sequence(N_PRACTICE_TRIALS, n_back_level)

for trial_idx in range(N_PRACTICE_TRIALS):
    asrt_pos = practice_positions[trial_idx]
    nback_letter = practice_nback[trial_idx]

    fixation.draw()
    win.flip()
    core.wait(FIXATION_TIME)

    kb.clearEvents()
    trial_clock = core.Clock()
    while trial_clock.getTime() < STIM_TIMEOUT:
        draw_trial(asrt_pos, nback_letter)
        win.flip()
        keys = kb.getKeys(
            keyList=["s", "f", "j", "l", "space", "escape"],
            waitRelease=False,
            clear=False
        )
        for k in keys:
            if k.name == "escape":
                quit_experiment()

    win.flip()
    core.wait(ITI)

practice_done_text.draw()
win.flip()
wait_for_space()

# =========================
# OPEN PER-TRIAL CSV (incremental, per-block flush)
# =========================
csv_file = open(out_path, "w", newline="", encoding="utf-8-sig")
csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
csv_writer.writeheader()
csv_file.flush()

# =========================
# RUN EXPERIMENT
# =========================
global_trial_counter = 0

for block in range(1, N_BLOCKS + 1):
    block_seq = get_asrt_sequence_for_block()
    block_nback = get_nback_sequence(TRIALS_PER_BLOCK, n_back_level)

    prev_positions = []
    block_rows = []

    # Vekteo's initialDelay: blank ~1s before the first stim of each block
    win.flip()
    core.wait(INITIAL_DELAY)

    for trial_idx in range(TRIALS_PER_BLOCK):
        global_trial_counter += 1

        asrt_pos = block_seq[trial_idx]
        asrt_key = POS_KEYS[asrt_pos]
        nback_letter = block_nback[trial_idx]

        nback_target = 0
        if trial_idx >= n_back_level and block_nback[trial_idx] == block_nback[trial_idx - n_back_level]:
            nback_target = 1

        fixation.draw()
        win.flip()
        core.wait(FIXATION_TIME)

        kb.clearEvents()
        trial_clock = core.Clock()

        asrt_response = None
        asrt_rt = None
        asrt_correct = 0
        nback_response = 0

        responded_asrt = False

        # Fixed SOA: trial always runs the full STIM_TIMEOUT regardless of responses,
        # to keep stimulus-onset-asynchrony constant across trials.
        while trial_clock.getTime() < STIM_TIMEOUT:
            draw_trial(asrt_pos, nback_letter)
            win.flip()

            keys = kb.getKeys(
                keyList=["s", "f", "j", "l", "space", "escape"],
                waitRelease=False,
                clear=False
            )

            for k in keys:
                if k.name == "escape":
                    quit_experiment()

                if k.name in ["s", "f", "j", "l"] and not responded_asrt:
                    asrt_response = k.name
                    asrt_rt = k.rt
                    responded_asrt = True
                    asrt_correct = int(asrt_response == asrt_key)

                if k.name == "space":
                    nback_response = 1

        # if no ASRT response, mark missing (None -> empty cell, NaN in pandas)
        if asrt_response is None:
            asrt_response = ""
            asrt_rt = None
            asrt_correct = 0

        nback_correct = int(nback_response == nback_target)

        prev2 = prev_positions[-2] if len(prev_positions) >= 2 else None
        prev1 = prev_positions[-1] if len(prev_positions) >= 1 else None
        triplet_str, triplet_type = classify_triplet(prev2, prev1, asrt_pos)

        prev_positions.append(asrt_pos)

        # vekteo convention: trial 1 = random lead-in, then patterns at even trial
        # numbers (2, 4, ...) and randoms at odd (3, 5, ...). trial_idx is 0-based.
        trial_number_1based = trial_idx + 1
        p_or_r = "P" if (trial_number_1based >= 2 and trial_number_1based % 2 == 0) else "R"

        row = {
            "participant": participant,
            "condition": condition,
            "n_back_level": n_back_level,
            "block": block,
            "trial_in_block": trial_number_1based,
            "global_trial": global_trial_counter,
            "p_or_r": p_or_r,
            "asrt_position": asrt_pos,
            "asrt_correct_key": asrt_key,
            "asrt_response": asrt_response,
            "asrt_correct": asrt_correct,
            "asrt_rt": asrt_rt,
            "nback_letter": nback_letter,
            "nback_target": nback_target,
            "nback_response": nback_response,
            "nback_correct": nback_correct,
            "triplet": triplet_str,
            "triplet_type": triplet_type,
            "probe_focus": "",
            "probe_content": "",
            "probe_spontaneous": ""
        }
        block_rows.append(row)

        win.flip()
        core.wait(ITI)

    # -------------------------
    # Thought probes after block
    # -------------------------
    probe_focus = run_probe(
        rtl(
            "עד כמה היית מרוכז/ת במשימה ממש לפני הופעת השאלה?\n\n"
            "1 = בכלל לא\n2 = מעט\n3 = די מרוכז/ת\n4 = מאוד"
        ),
        ["1", "2", "3", "4"]
    )

    probe_content = run_probe(
        rtl(
            "אם לא היית מרוכז/ת לגמרי, מה הכי תיאר את החוויה שלך?\n\n"
            "1 = מחשבות בעלות תוכן\n"
            "2 = ריק מנטלי / blank\n"
            "3 = לא בטוח/ה\n"
            "4 = הייתי ממוקד/ת במשימה"
        ),
        ["1", "2", "3", "4"]
    )

    probe_spontaneous = run_probe(
        rtl(
            "אם הקשב שלך נדד, האם זה קרה באופן:\n\n"
            "1 = ספונטני\n2 = מכוון\n3 = גם וגם\n4 = לא נדד"
        ),
        ["1", "2", "3", "4"]
    )

    # attach probe values to this block's rows and write them to disk now
    for row in block_rows:
        row["probe_focus"] = probe_focus
        row["probe_content"] = probe_content
        row["probe_spontaneous"] = probe_spontaneous
        csv_writer.writerow(row)
    csv_file.flush()

    # Per-block ASRT feedback (vekteo-style: accuracy + mean RT, ~5s display)
    if SHOW_BLOCK_FEEDBACK:
        correct_rows = [r for r in block_rows if r["asrt_correct"] == 1]
        accuracy_pct = round(len(correct_rows) / len(block_rows) * 100)
        rts = [r["asrt_rt"] for r in correct_rows if r["asrt_rt"] is not None]
        mean_rt_ms = round(sum(rts) / len(rts) * 1000) if rts else 0
        if accuracy_pct < 90:
            msg = "נסה/י להיות מדויק/ת יותר."
        elif mean_rt_ms > 350:
            msg = "אפשר לנסות לענות מהר יותר."
        else:
            msg = "המשך/י כך!"
        feedback_text.text = rtl(
            f"סיום בלוק {block}\n\n"
            f"דיוק: {accuracy_pct}%\n"
            f"זמן תגובה ממוצע: {mean_rt_ms} ms\n\n"
            f"{msg}"
        )
        feedback_text.draw()
        win.flip()
        core.wait(5.0)

    # Between-block break (skip after the last block — awareness comes next)
    if block < N_BLOCKS:
        break_text.text = rtl(
            f"סיימת בלוק {block} מתוך {N_BLOCKS}.\n\n"
            "אפשר לקחת הפסקה קצרה.\n\n"
            "לחצ/י SPACE כדי להמשיך."
        )
        break_text.draw()
        win.flip()
        wait_for_space()

# done writing per-trial data
csv_file.close()

# =========================
# AWARENESS QUESTION (saved to session sidecar CSV)
# =========================
kb.clearEvents()
while True:
    awareness_question.draw()
    win.flip()
    keys = kb.getKeys(keyList=["y", "n", "escape"], waitRelease=False)
    if keys:
        if keys[0].name == "escape":
            win.close()
            core.quit()
        awareness_response = keys[0].name
        break

session_fields = [
    "participant", "age", "vision", "condition", "n_back_level",
    "timestamp", "awareness_response"
]
with open(session_path, "w", newline="", encoding="utf-8-sig") as sf:
    session_writer = csv.DictWriter(sf, fieldnames=session_fields)
    session_writer.writeheader()
    session_writer.writerow({
        "participant": participant,
        "age": age,
        "vision": vision,
        "condition": condition,
        "n_back_level": n_back_level,
        "timestamp": timestamp,
        "awareness_response": awareness_response,
    })

# =========================
# END
# =========================
end_text.draw()
win.flip()
wait_for_space()

win.close()
core.quit()