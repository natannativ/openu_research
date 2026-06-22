# -*- coding: utf-8 -*-
from psychopy import visual, core, gui, data
from psychopy.hardware import keyboard
from bidi.algorithm import get_display
import random
import csv
import os

def rtl(text):
    return "\n".join(get_display(line) for line in text.split("\n"))

HEBREW_FONT = "Arial Hebrew"
KEY_S = "S"
KEY_F = "F"
KEY_J = "J"
KEY_L = "L"

# =========================
# SETTINGS
# =========================
# Full run: 20 blocks * 32 trials (~27 min). short_version overrides to a pilot.
N_BLOCKS = 20
N_SEQUENCE_REPS = 4
TRIALS_PER_BLOCK = N_SEQUENCE_REPS * 8   # 8 trials per cycle (4 P + 4 R) -> 32
N_PRACTICE_TRIALS = 40                   # not saved

SHORT_N_BLOCKS = 1
SHORT_N_SEQUENCE_REPS = 2
SHORT_N_PRACTICE_TRIALS = 8

ITI = 0.12                     # blank gap between trials (s)
INITIAL_DELAY = 1.0            # before the first stim of each block (s)
NBACK_RESPONSE_WINDOW = 1.2    # fixed window from letter onset to press SPACE (s)
ASRT_MAX_ATTEMPTS = 15         # safety cap on the correction loop
NBACK_WARNING_THRESHOLD = 0.5  # warn if block n-back hit rate falls below this
PRACTICE_NBACK_FEEDBACK = True
PRACTICE_MIN_ASRT_ACC = 0.60   # repeat practice if ASRT accuracy is below this
PRACTICE_MIN_NBACK_HIT = 0.50  # ...or if the n-back hit rate is below this
PRACTICE_MAX_ATTEMPTS = 3      # cap on practice repeats
SHOW_BLOCK_FEEDBACK = True
PROBE_SCALE = ["1", "2", "3", "4"]

# 24 permutations of [1,2,3,4]; per-participant pattern chosen from these (counterbalancing).
ASRT_SEQUENCES = [
    [1, 2, 3, 4], [1, 2, 4, 3], [1, 3, 2, 4], [1, 3, 4, 2], [1, 4, 2, 3], [1, 4, 3, 2],
    [2, 1, 3, 4], [2, 1, 4, 3], [2, 3, 1, 4], [2, 3, 4, 1], [2, 4, 1, 3], [2, 4, 3, 1],
    [3, 1, 2, 4], [3, 1, 4, 2], [3, 2, 1, 4], [3, 2, 4, 1], [3, 4, 1, 2], [3, 4, 2, 1],
    [4, 1, 2, 3], [4, 1, 3, 2], [4, 2, 1, 3], [4, 2, 3, 1], [4, 3, 1, 2], [4, 3, 2, 1],
]

POS_KEYS = {1: "s", 2: "f", 3: "j", 4: "l"}
POS_COORDS = {1: (-0.45, 0.0), 2: (-0.15, 0.0), 3: (0.15, 0.0), 4: (0.45, 0.0)}

NBACK_STIMULI = ["A", "B", "C", "D", "E", "F"]
NBACK_TARGET_RATE = 0.25       # target rate on eligible trials

# =========================
# PARTICIPANT INFO
# =========================
info = {
    "participant": "",
    "age": "",
    "gender": ["female", "male", "other"],
    "ADHD": ["no", "yes", "unsure"],
    "condition": ["low_load", "high_load"],   # low = 1-back, high = 2-back
    "short_version": False,
    "fullscreen": True
}

dlg = gui.DlgFromDict(
    info,
    title="ASRT + Mind Wandering + Visual n-back",
    order=["participant", "age", "gender", "ADHD", "condition", "short_version", "fullscreen"],
    sortKeys=False,
)
if not dlg.OK:
    core.quit()

participant = info["participant"]
age = info["age"]
gender = info["gender"]
adhd = info["ADHD"]
condition = info["condition"]
short_version = info["short_version"]
fullscreen = info["fullscreen"]

n_back_level = 1 if condition == "low_load" else 2

if n_back_level == 1:
    nback_step_phrase = "לאות הקודמת"
elif n_back_level == 2:
    nback_step_phrase = "לאות שהופיעה שתי אותיות אחורה"
else:
    nback_step_phrase = f"לאות שהופיעה {n_back_level} אותיות אחורה"

# Reproducible per-participant sequence; random for non-numeric ids.
def select_asrt_sequence(participant_id):
    try:
        n = int(str(participant_id).strip())
        return ASRT_SEQUENCES[(n - 1) % len(ASRT_SEQUENCES)]
    except (ValueError, TypeError):
        return random.choice(ASRT_SEQUENCES)

ASRT_PATTERN = select_asrt_sequence(participant)
ASRT_SEQUENCE_STR = "".join(str(p) for p in ASRT_PATTERN)

if short_version:
    N_BLOCKS = SHORT_N_BLOCKS
    N_SEQUENCE_REPS = SHORT_N_SEQUENCE_REPS
    TRIALS_PER_BLOCK = N_SEQUENCE_REPS * 8
    N_PRACTICE_TRIALS = SHORT_N_PRACTICE_TRIALS

# =========================
# DATA FILE
# =========================
timestamp = data.getDateStr()
filename = f"data_{participant}_{condition}_{timestamp}.csv"
out_path = os.path.join(os.getcwd(), filename)

fieldnames = [
    "participant", "condition", "n_back_level", "asrt_sequence",
    "block", "epoch", "trial_in_block", "global_trial",
    "p_or_r",  # "P" pattern / "R" random
    "asrt_position", "asrt_correct_key", "asrt_response", "asrt_correct", "asrt_rt",
    "asrt_n_attempts",
    "nback_letter", "nback_target", "nback_response", "nback_correct",
    "after_letter_test",  # 1 if the previous trial triggered a miss gate (exclude from RT)
    "triplet", "triplet_type",
    "probe_focus", "probe_content", "probe_spontaneous"
]
# awareness is collected once per session in a sidecar file
session_filename = f"session_{participant}_{condition}_{timestamp}.csv"
session_path = os.path.join(os.getcwd(), session_filename)

# =========================
# WINDOW AND STIMULI
# =========================
win = visual.Window(
    size=[1400, 900],
    fullscr=fullscreen,
    color="black",
    units="height",
    useRetina=True  # full pixel density so text isn't blurry on Mac Retina
)
win.mouseVisible = False

kb = keyboard.Keyboard()

# Constant grid of 4 outline circles; active target is a filled circle on top.
PLACEHOLDER_RADIUS = 0.025
placeholder_stims = [
    visual.Circle(
        win, radius=PLACEHOLDER_RADIUS, pos=POS_COORDS[p],
        fillColor=None, lineColor="gray", lineWidth=2, edges=64
    )
    for p in (1, 2, 3, 4)
]
target_stim = visual.Circle(win, radius=PLACEHOLDER_RADIUS, fillColor="white", lineColor="white")
nback_text = visual.TextStim(win, text="", pos=(0, 0.18), color="white", height=0.05)

if n_back_level == 0:
    nback_paragraph = (
        "בנוסף, תופיע במרכז המסך אות.\n"
        "בתנאי זה אין צורך להגיב לאות — אפשר להתעלם ממנה.\n\n"
    )
else:
    nback_paragraph = (
        "בנוסף, תופיע במרכז המסך אות.\n"
        f"אם האות הנוכחית זהה {nback_step_phrase} — לחצ/י רווח.\n\n"
    )

instructions = visual.TextStim(
    win,
    text=rtl(
        "ברוך/ה הבא/ה לניסוי.\n\n"
        "בכל ניסיון יופיע עיגול לבן באחד מארבעה מיקומים.\n"
        "לחצ/י מהר ובמדויק על המקש המתאים:\n\n"
        f"שמאל חיצוני — מקש {KEY_S}\n"
        f"שמאל פנימי — מקש {KEY_F}\n"
        f"ימין פנימי — מקש {KEY_J}\n"
        f"ימין חיצוני — מקש {KEY_L}\n\n"
        + nback_paragraph +
        "אחרי כל בלוק יופיעו כמה שאלות קצרות.\n\n"
        "לחצ/י על מקש הרווח כדי להתחיל."
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
        "במטלה היה דפוס נסתר במיקומי העיגול —\n"
        f"לסירוגין מיקום קבוע (לפי הסדר {'→'.join(str(p) for p in ASRT_PATTERN)}) ומיקום אקראי.\n"
        "אנו בודקים האם אנשים לומדים דפוסים סטטיסטיים כאלה ללא מודעות,\n"
        "וכיצד עומס קוגניטיבי (מטלת הזיכרון של האותיות) משפיע על למידה זו.\n\n"
        "אם יש לך שאלות לגבי המחקר, ניתן לפנות לחוקרים.\n\n"
        "לחצ/י על מקש הרווח לסיום."
    ),
    color="white",
    height=0.03,
    wrapWidth=1.6,
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

if n_back_level == 0:
    practice_nback_line = "במרכז תופיע אות — אפשר להתעלם ממנה.\n\n"
else:
    practice_nback_line = (
        f"במרכז תופיע אות; אם היא זהה {nback_step_phrase} — לחצ/י רווח.\n\n"
    )

practice_instructions = visual.TextStim(
    win,
    text=rtl(
        "נתחיל בתרגול קצר.\n\n"
        "כשמופיע עיגול — לחצ/י על המקש שמתאים למיקום שלו:\n\n"
        f"שמאל חיצוני — מקש {KEY_S}\n"
        f"שמאל פנימי — מקש {KEY_F}\n"
        f"ימין פנימי — מקש {KEY_J}\n"
        f"ימין חיצוני — מקש {KEY_L}\n\n"
        + practice_nback_line +
        "התרגול אינו נשמר.\n\n"
        "לחצ/י על אחד ממקשי התגובה כדי להתחיל."
    ),
    color="white",
    height=0.035,
    wrapWidth=1.2,
    font=HEBREW_FONT
)

practice_done_text = visual.TextStim(
    win,
    text=rtl("התרגול הסתיים.\n\nלחצ/י על אחד ממקשי התגובה להתחלת המטלה האמיתית."),
    color="white",
    height=0.04,
    wrapWidth=1.2,
    font=HEBREW_FONT
)

practice_retry_text = visual.TextStim(
    win,
    text="",
    color="white",
    height=0.04,
    wrapWidth=1.4,
    font=HEBREW_FONT
)

break_text = visual.TextStim(
    win,
    text="",
    color="white",
    height=0.04,
    wrapWidth=1.2,
    font=HEBREW_FONT
)

# Per-block feedback (accuracy + mean RT).
feedback_text = visual.TextStim(
    win,
    text="",
    color="white",
    height=0.04,
    wrapWidth=1.4,
    font=HEBREW_FONT
)

# Low n-back accuracy warning.
nback_warning_text = visual.TextStim(
    win,
    text="",
    color="red",
    height=0.045,
    wrapWidth=1.4,
    font=HEBREW_FONT
)

# Immediate per-trial n-back feedback (practice only).
nback_practice_fb = visual.TextStim(
    win,
    text="",
    color="white",
    height=0.045,
    pos=(0, -0.2),
    wrapWidth=1.4,
    font=HEBREW_FONT
)

# Mind-wandering probe / explanation screens.
mw_text = visual.TextStim(
    win,
    text="",
    color="white",
    height=0.032,
    wrapWidth=1.5,
    font=HEBREW_FONT
)

# Gate shown when a target letter repeat is missed in the real task.
nback_miss_text = visual.TextStim(
    win,
    text=rtl(
        "פספסת את האות!\n\n"
        "האות חזרה ולא לחצת רווח.\n"
        "חשוב לעקוב אחרי האות במרכז המסך.\n\n"
        "נתחיל לספור מחדש מהאות הבאה.\n\n"
        "לחצ/י על אחד ממקשי התגובה כדי להמשיך."
    ),
    color="red",
    height=0.04,
    wrapWidth=1.4,
    font=HEBREW_FONT
)

# =========================
# HELPERS
# =========================
def draw_placeholders():
    for c in placeholder_stims:
        c.draw()

def draw_trial(position, letter):
    draw_placeholders()
    target_stim.pos = POS_COORDS[position]
    target_stim.draw()
    nback_text.text = letter
    nback_text.draw()

def present_pre_target(is_first_trial):
    # Grid only, no target: INITIAL_DELAY before the first trial, RSI otherwise.
    draw_placeholders()
    win.flip()
    core.wait(INITIAL_DELAY if is_first_trial else ITI)

def run_asrt_nback_trial(asrt_pos, nback_letter):
    """Run one ASRT + n-back trial and return its responses.

    Incorrect s/f/j/l presses keep the target on screen until the correct key
    (correction loop). SPACE is accepted any time during the trial so a press is
    never lost. NBACK_RESPONSE_WINDOW is a fixed minimum trial length from letter
    onset. Scoring uses the first ASRT keypress; ASRT_MAX_ATTEMPTS is a safety cap.
    """
    asrt_key = POS_KEYS[asrt_pos]

    kb.clearEvents()
    kb.clock.reset()      # key.rt measured from letter onset
    clock = core.Clock()

    asrt_response = None
    asrt_rt = None
    asrt_correct = 0
    asrt_n_attempts = 0
    nback_response = 0

    first_recorded = False
    correct_given = False

    while True:
        now = clock.getTime()

        draw_placeholders()
        if not correct_given:
            target_stim.pos = POS_COORDS[asrt_pos]
            target_stim.draw()
        nback_text.text = nback_letter
        nback_text.draw()
        win.flip()

        keys = kb.getKeys(keyList=["s", "f", "j", "l", "space", "escape"], waitRelease=False)
        for k in keys:
            if k.name == "escape":
                quit_experiment()
            elif k.name in ("s", "f", "j", "l"):
                asrt_n_attempts += 1
                if not first_recorded:
                    asrt_response = k.name
                    asrt_rt = k.rt
                    asrt_correct = int(k.name == asrt_key)
                    first_recorded = True
                if k.name == asrt_key and not correct_given:
                    correct_given = True
            elif k.name == "space" and not nback_response:
                nback_response = 1

        if correct_given and now >= NBACK_RESPONSE_WINDOW:
            break
        if asrt_n_attempts >= ASRT_MAX_ATTEMPTS and not correct_given:
            break

    return {
        "asrt_response": asrt_response,
        "asrt_rt": asrt_rt,
        "asrt_correct": asrt_correct,
        "asrt_n_attempts": asrt_n_attempts,
        "nback_response": nback_response,
    }

def trial_type(trial_number_1based):
    # Pattern at even trial numbers (>=2); random otherwise (trial 1 = lead-in).
    return "P" if (trial_number_1based >= 2 and trial_number_1based % 2 == 0) else "R"

def get_asrt_sequence_for_block():
    # Random lead-in (trial 1), then pattern/random alternating; ends on a
    # pattern (no trailing random). N_SEQUENCE_REPS * 8 trials total.
    seq = [random.choice([1, 2, 3, 4])]
    last_rep = N_SEQUENCE_REPS - 1
    for rep in range(N_SEQUENCE_REPS):
        for sp in range(4):
            seq.append(ASRT_PATTERN[sp])
            if not (rep == last_rep and sp == 3):
                seq.append(random.choice([1, 2, 3, 4]))
    return seq

def get_nback_sequence(trial_types, n_back):
    # Targets (letter repeats) only on RANDOM ("R") trials, so the letter task
    # never disturbs the pattern-triplet RTs.
    length = len(trial_types)
    if n_back == 0:
        return [random.choice(NBACK_STIMULI) for _ in range(length)]
    seq = []
    for i in range(length):
        if i < n_back:
            seq.append(random.choice(NBACK_STIMULI))
            continue
        ref = seq[i - n_back]
        is_random = (trial_types[i] == "R")
        if is_random and random.random() < NBACK_TARGET_RATE:
            seq.append(ref)
        else:
            non_targets = [s for s in NBACK_STIMULI if s != ref]
            seq.append(random.choice(non_targets))
    return seq

def is_nback_target(letters, index, anchor=0):
    # A target needs n_back_level real letters since the last reset (anchor),
    # so the stream restarts cleanly after a miss gate.
    return (n_back_level >= 1
            and index - anchor >= n_back_level
            and letters[index] == letters[index - n_back_level])

def reset_nback_window(letters, start, n_back):
    # After a reset, force the next n_back letters to be non-repeats so there is
    # no confusing visual repeat before the participant has rebuilt the stream.
    for j in range(start, min(start + n_back, len(letters))):
        ref = letters[j - n_back]
        if letters[j] == ref:
            letters[j] = random.choice([s for s in NBACK_STIMULI if s != ref])

def build_high_triplets():
    # P-x-P where pattern positions are consecutive (wrap-around); middle is any.
    high = set()
    bases = [(ASRT_PATTERN[i], ASRT_PATTERN[(i + 1) % 4]) for i in range(4)]
    for first, third in bases:
        for middle in [1, 2, 3, 4]:
            high.add((first, middle, third))
    return high

HIGH_TRIPLETS = build_high_triplets()

def classify_triplet(prev2, prev1, current):
    # H high, L low, R repetition, T trill, X exclude (vekteo labels).
    if prev2 is None or prev1 is None:
        return "", "X"
    tri = (prev2, prev1, current)
    tri_str = f"{tri[0]}_{tri[1]}_{tri[2]}"  # underscore so Excel won't read it as a date
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

def show_feedback(title, accuracy_pct, mean_rt_ms, nback_stats=None):
    if accuracy_pct < 90:
        msg = "נסה/י להיות מדויק/ת יותר."
    elif mean_rt_ms > 350:
        msg = "אפשר לנסות לענות מהר יותר."
    else:
        msg = "המשך/י כך!"

    lines = [
        title,
        "",
        "מטלת העיגול:",
        f"דיוק: {accuracy_pct}%",
        f"זמן תגובה ממוצע: {mean_rt_ms} מילישניות",
    ]

    if nback_stats is not None:
        n_targets, n_hits, n_misses, n_false_alarms = nback_stats
        lines += [
            "",
            "מטלת האות:",
            f"זיהית {n_hits} מתוך {n_targets} חזרות.",
            f"החמצות: {n_misses}, לחיצות מיותרות: {n_false_alarms}.",
        ]
        if n_targets > 0 and n_hits / n_targets < 0.6:
            msg = "שימי לב גם לאות במרכז — לחצי רווח כשהיא חוזרת."

    lines += ["", msg, "", "לחצ/י על אחד ממקשי התגובה כדי להמשיך."]
    feedback_text.text = rtl("\n".join(lines))
    feedback_text.draw()
    win.flip()
    core.wait(PROBE_SETTLE)  # so a prior keypress can't skip the screen
    wait_for_response_key()

def show_nback_practice_feedback(nback_target, nback_response):
    # No feedback for correct rejections (non-target, no press) to keep pace.
    if n_back_level < 1:
        return
    if nback_target == 1 and nback_response == 1:
        txt, col = "זיהית נכון! (רווח)", "lime"
    elif nback_target == 1 and nback_response == 0:
        txt, col = "פספסת — האות חזרה, היה צריך ללחוץ רווח", "red"
    elif nback_target == 0 and nback_response == 1:
        txt, col = "לחיצה מיותרת — האות לא חזרה", "orange"
    else:
        return
    nback_practice_fb.color = col
    nback_practice_fb.text = rtl(txt)
    nback_practice_fb.draw()
    win.flip()
    core.wait(0.9)

PROBE_SETTLE = 0.35  # ignore keys this long so a previous answer can't carry over (s)

def run_probe(question_text, allowed_keys):
    probe_text.text = question_text
    listen_keys = list(allowed_keys) + ["escape"]
    probe_text.draw()
    win.flip()
    core.wait(PROBE_SETTLE)
    kb.clearEvents()
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

def wait_for_response_key():
    kb.clearEvents()
    while True:
        keys = kb.getKeys(keyList=["s", "f", "j", "l", "escape"], waitRelease=False)
        if keys:
            if keys[0].name == "escape":
                quit_experiment()
            return

def show_nback_miss_gate():
    nback_miss_text.draw()
    win.flip()
    core.wait(PROBE_SETTLE)
    wait_for_response_key()

def show_mw_info(body):
    mw_text.text = rtl(body + "\n\nלחצ/י על מקש הרווח כדי להמשיך.")
    mw_text.draw()
    win.flip()
    core.wait(PROBE_SETTLE)
    wait_for_space()

# =========================
# START
# =========================
instructions.draw()
win.flip()
wait_for_space()

# =========================
# PRACTICE BLOCK (random positions, NOT saved)
# =========================
def run_practice_once():
    practice_positions = [random.choice([1, 2, 3, 4]) for _ in range(N_PRACTICE_TRIALS)]
    practice_nback = get_nback_sequence(["R"] * N_PRACTICE_TRIALS, n_back_level)

    correct_count = 0
    rts = []
    nb_targets = 0
    nb_hits = 0

    for trial_idx in range(N_PRACTICE_TRIALS):
        present_pre_target(trial_idx == 0)
        nb_target = int(is_nback_target(practice_nback, trial_idx))
        result = run_asrt_nback_trial(practice_positions[trial_idx], practice_nback[trial_idx])

        correct_count += result["asrt_correct"]
        if result["asrt_correct"] and result["asrt_rt"] is not None:
            rts.append(result["asrt_rt"])
        if nb_target:
            nb_targets += 1
            nb_hits += int(result["nback_response"] == 1)

        if PRACTICE_NBACK_FEEDBACK:
            show_nback_practice_feedback(nb_target, result["nback_response"])

        draw_placeholders()
        win.flip()

    asrt_acc = correct_count / N_PRACTICE_TRIALS
    nb_hit_rate = (nb_hits / nb_targets) if nb_targets > 0 else 1.0
    mean_rt_ms = round(sum(rts) / len(rts) * 1000) if rts else 0
    return asrt_acc, nb_hit_rate, mean_rt_ms

def practice_passed(asrt_acc, nb_hit_rate):
    if asrt_acc < PRACTICE_MIN_ASRT_ACC:
        return False
    if n_back_level >= 1 and nb_hit_rate < PRACTICE_MIN_NBACK_HIT:
        return False
    return True

for practice_attempt in range(1, PRACTICE_MAX_ATTEMPTS + 1):
    practice_instructions.draw()
    win.flip()
    wait_for_response_key()

    asrt_acc, nb_hit_rate, mean_rt_ms = run_practice_once()

    if SHOW_BLOCK_FEEDBACK:
        show_feedback("סיום התרגול", round(asrt_acc * 100), mean_rt_ms)

    if practice_passed(asrt_acc, nb_hit_rate) or practice_attempt == PRACTICE_MAX_ATTEMPTS:
        break

    practice_retry_text.text = rtl(
        "התרגול עוד לא הצליח מספיק.\n\n"
        "נחזור עליו פעם נוספת כדי לוודא שהמטלה ברורה.\n\n"
        "לחצ/י על אחד ממקשי התגובה כדי להתחיל שוב."
    )
    practice_retry_text.draw()
    win.flip()
    wait_for_response_key()

practice_done_text.draw()
win.flip()
wait_for_response_key()

# =========================
# MIND-WANDERING PROBE EXPLANATION
# =========================
show_mw_info(
    "במהלך המטלה נעצור מדי פעם ונשאל 3 שאלות קצרות.\n\n"
    "השאלות מתייחסות למה שהיה לך בראש ממש לפני שהמסך נעצר.\n\n"
    "אין תשובה טובה או רעה — פשוט ענה/י לפי מה שבאמת קרה."
)

show_mw_info(
    "שאלה 1 — ריכוז:\n"
    "עד כמה היית מרוכז/ת במשימה?\n\n"
    "1 = בכלל לא    2 = מעט    3 = די מרוכז/ת    4 = מאוד מרוכז/ת\n\n"
    "אם חשבת על דברים אחרים — בחר/י 1 או 2.\n"
    "אם היית מרוכז/ת במטלה — בחר/י 3 או 4."
)

show_mw_info(
    "אם תשומת הלב שלך לא הייתה ממוקדת לגמרי במטלה,\n"
    "מה הכי מתאים למה שעבר לך בראש?\n\n"
    "1 = הראש היה ריק לגמרי — לא חשבתי על שום דבר מסוים\n"
    "2 = הראש היה בעיקר ריק — אולי הייתה מחשבה קצרה או לא ברורה\n"
    "3 = בעיקר מחשבה על משהו מסוים\n"
    "4 = חשבתי על משהו מסוים וברור"
)

show_mw_info(
    "האם מיקוד הקשב שלך — במטלה או מחוץ למטלה —\n"
    "היה מכוון או התרחש באופן ספונטני?\n\n"
    "1 = התרחש לגמרי באופן ספונטני\n"
    "2 = בעיקר ספונטני\n"
    "3 = בעיקר מכוון\n"
    "4 = מכוון לגמרי"
)

show_mw_info("עכשיו מתחילים את המטלה האמיתית.")

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

# Positions of correctly-answered trials; triplets use the last two + current.
correct_positions = []

for block in range(1, N_BLOCKS + 1):
    block_seq = get_asrt_sequence_for_block()
    block_trial_types = [trial_type(t) for t in range(1, TRIALS_PER_BLOCK + 1)]
    block_nback = get_nback_sequence(block_trial_types, n_back_level)
    epoch = (block - 1) // 4 + 1  # 5 epochs of 4 blocks

    block_rows = []
    prev_trial_gated = False
    nback_anchor = 0  # n-back counting restarts here after a miss gate

    for trial_idx in range(TRIALS_PER_BLOCK):
        global_trial_counter += 1

        asrt_pos = block_seq[trial_idx]
        asrt_key = POS_KEYS[asrt_pos]
        nback_letter = block_nback[trial_idx]
        nback_target = int(is_nback_target(block_nback, trial_idx, nback_anchor))

        present_pre_target(trial_idx == 0)
        result = run_asrt_nback_trial(asrt_pos, nback_letter)

        asrt_response = result["asrt_response"]
        asrt_rt = result["asrt_rt"]
        asrt_correct = result["asrt_correct"]
        asrt_n_attempts = result["asrt_n_attempts"]
        nback_response = result["nback_response"]
        nback_correct = int(nback_response == nback_target)

        trial_number_1based = trial_idx + 1
        p_or_r = trial_type(trial_number_1based)
        after_letter_test = 1 if prev_trial_gated else 0

        # X until there are two prior correct trials (and for the first two).
        if trial_number_1based <= 2 or len(correct_positions) < 2:
            triplet_str, triplet_type = "", "X"
        else:
            triplet_str, triplet_type = classify_triplet(
                correct_positions[-2], correct_positions[-1], asrt_pos
            )

        if asrt_correct == 1:
            correct_positions.append(asrt_pos)

        row = {
            "participant": participant,
            "condition": condition,
            "n_back_level": n_back_level,
            "asrt_sequence": ASRT_SEQUENCE_STR,
            "block": block,
            "epoch": epoch,
            "trial_in_block": trial_number_1based,
            "global_trial": global_trial_counter,
            "p_or_r": p_or_r,
            "asrt_position": asrt_pos,
            "asrt_correct_key": asrt_key,
            "asrt_response": asrt_response,
            "asrt_correct": asrt_correct,
            "asrt_rt": asrt_rt,
            "asrt_n_attempts": asrt_n_attempts,
            "nback_letter": nback_letter,
            "nback_target": nback_target,
            "nback_response": nback_response,
            "nback_correct": nback_correct,
            "after_letter_test": after_letter_test,
            "triplet": triplet_str,
            "triplet_type": triplet_type,
            "probe_focus": "",
            "probe_content": "",
            "probe_spontaneous": ""
        }
        block_rows.append(row)

        draw_placeholders()
        win.flip()

        # Gate on a missed target (no SPACE) before the next trial, then reset
        # the n-back stream so the participant starts counting fresh.
        this_trial_gated = (nback_target == 1 and nback_response == 0)
        if this_trial_gated:
            show_nback_miss_gate()
            nback_anchor = trial_idx + 1
            reset_nback_window(block_nback, trial_idx + 1, n_back_level)
        prev_trial_gated = this_trial_gated

    probe_focus = run_probe(
        rtl(
            "עד כמה היית מרוכז/ת במשימה ממש לפני שהשאלה הופיעה?\n\n"
            "1 = בכלל לא\n2 = מעט\n3 = די מרוכז/ת\n4 = מאוד מרוכז/ת"
        ),
        PROBE_SCALE
    )

    probe_content = run_probe(
        rtl(
            "אם תשומת הלב שלך לא הייתה ממוקדת לגמרי במטלה,\n"
            "מה הכי מתאים למה שעבר לך בראש?\n\n"
            "1 = הראש היה ריק לגמרי — לא חשבתי על שום דבר מסוים\n"
            "2 = הראש היה בעיקר ריק — אולי הייתה מחשבה קצרה או לא ברורה\n"
            "3 = בעיקר מחשבה על משהו מסוים\n"
            "4 = חשבתי על משהו מסוים וברור"
        ),
        PROBE_SCALE
    )

    probe_spontaneous = run_probe(
        rtl(
            "האם מיקוד הקשב שלך — במטלה או מחוץ למטלה —\n"
            "היה מכוון או התרחש באופן ספונטני?\n\n"
            "1 = התרחש לגמרי באופן ספונטני\n"
            "2 = בעיקר ספונטני\n"
            "3 = בעיקר מכוון\n"
            "4 = מכוון לגמרי"
        ),
        PROBE_SCALE
    )

    for row in block_rows:
        row["probe_focus"] = probe_focus
        row["probe_content"] = probe_content
        row["probe_spontaneous"] = probe_spontaneous
        csv_writer.writerow(row)
    csv_file.flush()

    nback_stats = None
    if n_back_level >= 1:
        n_targets = sum(1 for r in block_rows if r["nback_target"] == 1)
        n_hits = sum(1 for r in block_rows
                     if r["nback_target"] == 1 and r["nback_response"] == 1)
        n_misses = n_targets - n_hits
        n_false_alarms = sum(1 for r in block_rows
                             if r["nback_target"] == 0 and r["nback_response"] == 1)
        nback_stats = (n_targets, n_hits, n_misses, n_false_alarms)

    if SHOW_BLOCK_FEEDBACK:
        correct_rows = [r for r in block_rows if r["asrt_correct"] == 1]
        accuracy_pct = round(len(correct_rows) / len(block_rows) * 100)
        rts = [r["asrt_rt"] for r in correct_rows if r["asrt_rt"] is not None]
        mean_rt_ms = round(sum(rts) / len(rts) * 1000) if rts else 0
        show_feedback(f"סיום בלוק {block}", accuracy_pct, mean_rt_ms, nback_stats)

    if nback_stats is not None:
        n_targets, n_hits, n_misses, n_false_alarms = nback_stats
        hit_rate = (n_hits / n_targets) if n_targets > 0 else 1.0
        if hit_rate < NBACK_WARNING_THRESHOLD:
            nback_warning_text.text = rtl(
                "שימי לב!\n\n"
                f"זיהית רק {n_hits} מתוך {n_targets} חזרות של האות.\n"
                "חשוב לעקוב גם אחרי האות במרכז המסך,\n"
                f"וללחוץ רווח בכל פעם שהיא זהה {nback_step_phrase}.\n\n"
                "לחצ/י על אחד ממקשי התגובה כדי להמשיך."
            )
            nback_warning_text.draw()
            win.flip()
            wait_for_response_key()

    if block < N_BLOCKS:
        break_text.text = rtl(
            f"סיימת בלוק {block} מתוך {N_BLOCKS}.\n\n"
            "אפשר לקחת הפסקה קצרה.\n\n"
            "לחצ/י על אחד ממקשי התגובה כדי להמשיך."
        )
        break_text.draw()
        win.flip()
        wait_for_response_key()

csv_file.close()

# =========================
# AWARENESS QUESTION (session sidecar CSV)
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

awareness_detail = ""
if awareness_response == "y":
    win.mouseVisible = True
    detail_dlg = gui.Dlg(title="פירוט")
    detail_dlg.addText("מה הבחנת? נסה/י לתאר בקצרה.")
    detail_dlg.addField("תיאור:", "")
    detail_dlg.show()
    if detail_dlg.OK and detail_dlg.data:
        awareness_detail = str(detail_dlg.data[0]).strip()
    win.mouseVisible = False

session_fields = [
    "participant", "age", "gender", "adhd", "condition", "n_back_level", "asrt_sequence",
    "timestamp", "awareness_response", "awareness_detail"
]
with open(session_path, "w", newline="", encoding="utf-8-sig") as sf:
    session_writer = csv.DictWriter(sf, fieldnames=session_fields)
    session_writer.writeheader()
    session_writer.writerow({
        "participant": participant,
        "age": age,
        "gender": gender,
        "adhd": adhd,
        "condition": condition,
        "n_back_level": n_back_level,
        "asrt_sequence": ASRT_SEQUENCE_STR,
        "timestamp": timestamp,
        "awareness_response": awareness_response,
        "awareness_detail": awareness_detail,
    })

# =========================
# END
# =========================
end_text.draw()
win.flip()
wait_for_space()

win.close()
core.quit()