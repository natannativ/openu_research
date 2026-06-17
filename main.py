# -*- coding: utf-8 -*-
from psychopy import visual, core, gui, data
from psychopy.hardware import keyboard
from bidi.algorithm import get_display
import random
import csv
import os

def rtl(text):
    # Apply the bidi algorithm per line so Hebrew displays RTL.
    return "\n".join(get_display(line) for line in text.split("\n"))

HEBREW_FONT = "Arial Hebrew"

# =========================
# SETTINGS
# =========================
# Full run: 25 blocks * 80 trials ~ 85 min. short_version overrides to a pilot.
N_BLOCKS = 25
N_SEQUENCE_REPS = 10                     # repetitions of the 4-item pattern per block
TRIALS_PER_BLOCK = N_SEQUENCE_REPS * 8   # 8 trials per cycle (4 P + 4 R)
N_PRACTICE_TRIALS = 80                   # random-position practice, not saved

SHORT_N_BLOCKS = 3
SHORT_N_SEQUENCE_REPS = 5                # 40 trials per block
SHORT_N_PRACTICE_TRIALS = 20

ITI = 0.12                     # RSI: blank gap between trials (vekteo rsi = 120 ms)
INITIAL_DELAY = 1.0            # delay before the first stim of each block
NBACK_RESPONSE_WINDOW = 1.5    # fixed window (from letter onset) to press SPACE
ASRT_MAX_ATTEMPTS = 15         # safety cap on the correction loop (vekteo limit)
NBACK_WARNING_THRESHOLD = 0.5  # warn if block n-back hit rate falls below this
PRACTICE_NBACK_FEEDBACK = True # immediate n-back feedback, practice only
SHOW_BLOCK_FEEDBACK = True
PROBE_SCALE = ["1", "2", "3", "4"]

# 24 permutations of [1,2,3,4]; the per-participant pattern is chosen from these
# (counterbalancing, as in vekteo/variables.js). ASRT_PATTERN is set after the dialog.
ASRT_SEQUENCES = [
    [1, 2, 3, 4], [1, 2, 4, 3], [1, 3, 2, 4], [1, 3, 4, 2], [1, 4, 2, 3], [1, 4, 3, 2],
    [2, 1, 3, 4], [2, 1, 4, 3], [2, 3, 1, 4], [2, 3, 4, 1], [2, 4, 1, 3], [2, 4, 3, 1],
    [3, 1, 2, 4], [3, 1, 4, 2], [3, 2, 1, 4], [3, 2, 4, 1], [3, 4, 1, 2], [3, 4, 2, 1],
    [4, 1, 2, 3], [4, 1, 3, 2], [4, 2, 1, 3], [4, 2, 3, 1], [4, 3, 1, 2], [4, 3, 2, 1],
]

POS_KEYS = {1: "s", 2: "f", 3: "j", 4: "l"}            # position -> response key
POS_COORDS = {1: (-0.45, 0.0), 2: (-0.15, 0.0), 3: (0.15, 0.0), 4: (0.45, 0.0)}

NBACK_STIMULI = ["A", "B", "C", "D", "E", "F"]
NBACK_TARGET_RATE = 0.25       # target rate on eligible trials

# =========================
# PARTICIPANT INFO
# =========================
info = {
    "participant": "",
    "age": "",
    "vision": ["normal", "corrected"],
    "condition": ["low_load", "high_load"],   # low = 0-back (ignore letter), high = 1-back
    "short_version": False,                   # piloting flag — shorter run
    "fullscreen": True
}

dlg = gui.DlgFromDict(info, title="ASRT + Mind Wandering + Visual n-back")
if not dlg.OK:
    core.quit()

participant = info["participant"]
age = info["age"]
vision = info["vision"]
condition = info["condition"]
short_version = info["short_version"]
fullscreen = info["fullscreen"]

n_back_level = 0 if condition == "low_load" else 1

# Reproducible per-participant sequence (random for non-numeric ids).
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
    "block", "trial_in_block", "global_trial",
    "p_or_r",  # "P" pattern / "R" random
    "asrt_position", "asrt_correct_key", "asrt_response", "asrt_correct", "asrt_rt",
    "asrt_n_attempts",
    "nback_letter", "nback_target", "nback_response", "nback_correct",
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
    units="height"
)
win.mouseVisible = False  # hide the mouse cursor during the experiment

kb = keyboard.Keyboard()

# Constant grid of 4 outline circles; the active target is a filled circle on top.
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
        "אם האות הנוכחית זהה לאות שהופיעה בניסיון הקודם — לחצ/י רווח.\n\n"
    )

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
        + nback_paragraph +
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
        f"במטלה היה דפוס נסתר במיקומי העיגול — לסירוגין, מיקום קבוע (לפי הסדר {'→'.join(str(p) for p in ASRT_PATTERN)}) ומיקום אקראי. "
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

if n_back_level == 0:
    practice_nback_line = "במרכז תופיע אות — אפשר להתעלם ממנה.\n\n"
else:
    practice_nback_line = (
        "במרכז תופיע אות; אם היא זהה לאות מהניסיון הקודם — לחצ/י רווח.\n\n"
    )

practice_instructions = visual.TextStim(
    win,
    text=rtl(
        "לפני המטלה האמיתית — בלוק תרגול קצר.\n\n"
        "עיגול יופיע באחד מ-4 מיקומים. לחצ/י S / F / J / L.\n"
        + practice_nback_line +
        "התרגול אינו נשמר. לחצ/י על מקש תגובה (S/F/J/L) כדי להתחיל."
    ),
    color="white",
    height=0.035,
    wrapWidth=1.2,
    font=HEBREW_FONT
)

practice_done_text = visual.TextStim(
    win,
    text=rtl("התרגול הסתיים.\n\nלחצ/י על מקש תגובה (S/F/J/L) להתחלת המטלה האמיתית."),
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

# Low n-back accuracy warning (high_load only). Text set per-block before drawing.
nback_warning_text = visual.TextStim(
    win,
    text="",
    color="red",
    height=0.045,
    wrapWidth=1.4,
    font=HEBREW_FONT
)

# Immediate per-trial n-back feedback (practice only). Color/text set per trial.
nback_practice_fb = visual.TextStim(
    win,
    text="",
    color="white",
    height=0.045,
    pos=(0, -0.2),
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
    """Run one ASRT + n-back trial; return its responses.

    The target + frozen letter appear together. Incorrect s/f/j/l presses keep
    the target on screen until the correct key is pressed (correction loop).

    The n-back response window is FIXED: SPACE counts only within
    NBACK_RESPONSE_WINDOW seconds from letter onset, and the letter stays
    visible for exactly that window regardless of ASRT speed. The trial ends
    once the correct ASRT key has been given AND the fixed window has elapsed.
    Scoring uses the FIRST keypress; ASRT_MAX_ATTEMPTS is a safety cap.
    """
    asrt_key = POS_KEYS[asrt_pos]

    kb.clearEvents()
    clock = core.Clock()  # t = 0 is letter onset

    asrt_response = None
    asrt_rt = None
    asrt_correct = 0
    asrt_n_attempts = 0
    nback_response = 0

    first_recorded = False
    correct_given = False

    while True:
        now = clock.getTime()
        letter_visible = now < NBACK_RESPONSE_WINDOW

        draw_placeholders()
        if not correct_given:
            target_stim.pos = POS_COORDS[asrt_pos]
            target_stim.draw()
        if letter_visible:
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
            elif k.name == "space" and letter_visible and not nback_response:
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

def get_nback_sequence(length, n_back):
    # 0-back: uniform random letters. n>=1: inject targets at NBACK_TARGET_RATE
    # on eligible trials, otherwise force a non-target.
    if n_back == 0:
        return [random.choice(NBACK_STIMULI) for _ in range(length)]
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

def is_nback_target(letters, index):
    return (n_back_level >= 1
            and index >= n_back_level
            and letters[index] == letters[index - n_back_level])

def build_high_triplets():
    # High triplets are P-x-P where the pattern positions are consecutive
    # (with wrap-around); the middle can be any position.
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

def show_feedback(title, accuracy_pct, mean_rt_ms, nback_stats=None):
    # ~5 s feedback: ASRT accuracy + mean RT, plus n-back summary if provided.
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
        f"זמן תגובה ממוצע: {mean_rt_ms} ms",
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

    lines += ["", msg]
    feedback_text.text = rtl("\n".join(lines))
    feedback_text.draw()
    win.flip()
    core.wait(5.0)

def show_nback_practice_feedback(nback_target, nback_response):
    # Practice-only: brief flash so participants learn the letter task.
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

PROBE_SETTLE = 0.35  # ignore keys this long so the previous answer can't carry over

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
    # Self-paced screens advance on any response key.
    kb.clearEvents()
    while True:
        keys = kb.getKeys(keyList=["s", "f", "j", "l", "escape"], waitRelease=False)
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
wait_for_response_key()

practice_positions = [random.choice([1, 2, 3, 4]) for _ in range(N_PRACTICE_TRIALS)]
practice_nback = get_nback_sequence(N_PRACTICE_TRIALS, n_back_level)

practice_correct_count = 0
practice_rts = []

for trial_idx in range(N_PRACTICE_TRIALS):
    present_pre_target(trial_idx == 0)
    nb_target = int(is_nback_target(practice_nback, trial_idx))
    result = run_asrt_nback_trial(practice_positions[trial_idx], practice_nback[trial_idx])

    practice_correct_count += result["asrt_correct"]
    if result["asrt_correct"] and result["asrt_rt"] is not None:
        practice_rts.append(result["asrt_rt"])

    if PRACTICE_NBACK_FEEDBACK:
        show_nback_practice_feedback(nb_target, result["nback_response"])

    draw_placeholders()  # keep the grid up between trials
    win.flip()

if SHOW_BLOCK_FEEDBACK:
    practice_acc = round(practice_correct_count / N_PRACTICE_TRIALS * 100)
    practice_mean_rt = round(sum(practice_rts) / len(practice_rts) * 1000) if practice_rts else 0
    show_feedback("סיום התרגול", practice_acc, practice_mean_rt)

practice_done_text.draw()
win.flip()
wait_for_response_key()

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

# Targets of correctly-answered trials (whole session); triplets are built from
# the last two correct positions + current target (vekteo).
correct_positions = []

for block in range(1, N_BLOCKS + 1):
    block_seq = get_asrt_sequence_for_block()
    block_nback = get_nback_sequence(TRIALS_PER_BLOCK, n_back_level)

    block_rows = []

    for trial_idx in range(TRIALS_PER_BLOCK):
        global_trial_counter += 1

        asrt_pos = block_seq[trial_idx]
        asrt_key = POS_KEYS[asrt_pos]
        nback_letter = block_nback[trial_idx]
        nback_target = int(is_nback_target(block_nback, trial_idx))

        present_pre_target(trial_idx == 0)
        result = run_asrt_nback_trial(asrt_pos, nback_letter)

        asrt_response = result["asrt_response"]
        asrt_rt = result["asrt_rt"]
        asrt_correct = result["asrt_correct"]
        asrt_n_attempts = result["asrt_n_attempts"]
        nback_response = result["nback_response"]
        nback_correct = int(nback_response == nback_target)

        # Patterns sit at even trial numbers, randoms at odd (trial 1 = lead-in).
        trial_number_1based = trial_idx + 1
        p_or_r = "P" if (trial_number_1based >= 2 and trial_number_1based % 2 == 0) else "R"

        # Triplet from the last two correct positions + current target; X until
        # there are two prior correct trials (and for the first two trials).
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
            "triplet": triplet_str,
            "triplet_type": triplet_type,
            "probe_focus": "",
            "probe_content": "",
            "probe_spontaneous": ""
        }
        block_rows.append(row)

        draw_placeholders()  # keep the grid up between trials
        win.flip()

    # Thought probes after the block
    probe_focus = run_probe(
        rtl(
            "עד כמה היית מרוכז/ת במשימה ממש לפני הופעת השאלה?\n\n"
            "1 = בכלל לא\n2 = מעט\n3 = די מרוכז/ת\n4 = מאוד"
        ),
        PROBE_SCALE
    )

    probe_content = run_probe(
        rtl(
            "אם לא היית מרוכז/ת לגמרי, מה הכי תיאר את החוויה שלך?\n\n"
            "1 = מחשבות בעלות תוכן\n"
            "2 = ריק מנטלי / blank\n"
            "3 = לא בטוח/ה\n"
            "4 = הייתי ממוקד/ת במשימה"
        ),
        PROBE_SCALE
    )

    probe_spontaneous = run_probe(
        rtl(
            "אם הקשב שלך נדד, האם זה קרה באופן:\n\n"
            "1 = ספונטני\n2 = מכוון\n3 = גם וגם\n4 = לא נדד"
        ),
        PROBE_SCALE
    )

    # Attach the block's probe answers to its rows and write them out.
    for row in block_rows:
        row["probe_focus"] = probe_focus
        row["probe_content"] = probe_content
        row["probe_spontaneous"] = probe_spontaneous
        csv_writer.writerow(row)
    csv_file.flush()

    # n-back stats (high_load only): used for feedback and the warning.
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

    # Warn (self-paced) if n-back hit rate is too low.
    if nback_stats is not None:
        n_targets, n_hits, n_misses, n_false_alarms = nback_stats
        hit_rate = (n_hits / n_targets) if n_targets > 0 else 1.0
        if hit_rate < NBACK_WARNING_THRESHOLD:
            nback_warning_text.text = rtl(
                "שימי לב!\n\n"
                f"זיהית רק {n_hits} מתוך {n_targets} חזרות של האות.\n"
                "חשוב לעקוב גם אחרי האות במרכז המסך,\n"
                "וללחוץ רווח בכל פעם שהיא זהה לאות הקודמת.\n\n"
                "לחצ/י על מקש תגובה (S/F/J/L) כדי להמשיך."
            )
            nback_warning_text.draw()
            win.flip()
            wait_for_response_key()

    # Between-block break (skipped after the last block).
    if block < N_BLOCKS:
        break_text.text = rtl(
            f"סיימת בלוק {block} מתוך {N_BLOCKS}.\n\n"
            "אפשר לקחת הפסקה קצרה.\n\n"
            "לחצ/י על מקש תגובה (S/F/J/L) כדי להמשיך."
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

session_fields = [
    "participant", "age", "vision", "condition", "n_back_level", "asrt_sequence",
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
        "asrt_sequence": ASRT_SEQUENCE_STR,
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