"""Add difficulty tags (easy / medium / hard) to MelodyHub JSONL records.

The tag is written as its own control line right after the task line of the
record's input, for example::

    %%generation
    %%difficulty=easy

It has to be its own ``%%`` line: MelodyT5's encoder (``Patchilizer.encode``)
only keeps lines that start with ``%%`` or a header like ``K:`` as separate
units, and silently drops other text that contains no bar lines.

Difficulty is measured on the *output* melody only (the thing the model
learns to produce), using its notes rather than its headers or titles:
pitch range, leap size, accidentals, key signature, rhythmic variety, note
density, ornaments and tempo. Each feature is standardised over a random
sample of the data, combined with weights, and split into thirds.

Usage (from the repository root)::

    python ml/data_tagging/difficulty_tagging.py ml/data/melodyhub/train.jsonl ml/data/melodyhub/validation.jsonl

This writes ``train_tagged.jsonl`` and ``validation_tagged.jsonl`` next to the
inputs. Cut-offs are calibrated on the first file and reused for the rest, so
every file is tagged on the same scale.
"""
import argparse
import json
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

DIFFICULTIES = ("easy", "medium", "hard")

# Tasks whose output is a melody. Cataloging outputs metadata, so it is left untagged.
MELODY_TASKS = {"generation", "harmonization", "melodization", "segmentation", "transcription", "variation"}

WEIGHTS = {
    "pitch_range": 1.0,
    "mean_leap": 1.0,
    "accidentals": 1.0,
    "key_accidentals": 0.5,
    "rhythm_variety": 1.0,
    "notes_per_bar": 1.0,
    "ornaments": 0.5,
    "tempo": 0.5,
}

TASK_LINE_RE = re.compile(r"^%%\s*([A-Za-z]+)\s*$")
DIFFICULTY_LINE_RE = re.compile(r"^%%\s*difficulty\s*=.*$", re.I | re.M)
OLD_TAG_RE = re.compile(r"<\s*difficulty\s*=\s*\w+\s*>\s*", re.I)  # format from the previous script

HEADER_LINE_RE = re.compile(r"^\s*(?:[A-Za-z]:|%)")
INLINE_FIELD_RE = re.compile(r"\[[A-Za-z]:[^\]]*\]")
QUOTED_RE = re.compile(r'"[^"]*"')
DECORATION_RE = re.compile(r"![^!\n]*!|\+[^+\n]*\+")
NOTE_RE = re.compile(r"(\^{1,2}|_{1,2}|=)?([A-Ga-g])([,']*)(\d*/*\d*)")
BASE_SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

MAJOR_KEY_FIFTHS = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
                    "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6, "Cb": -7}
MODE_OFFSET = {"": 0, "maj": 0, "ion": 0, "mix": -1, "dor": -2, "m": -3, "min": -3,
               "aeo": -3, "phr": -4, "loc": -5, "lyd": 1}


# -------------------------
# Reading ABC
# -------------------------
def header_value(abc, field):
    """Last value of a header field such as K: or Q:, or None."""
    values = re.findall(rf"^{field}:\s*(.*)$", abc, flags=re.M)
    return values[-1].strip() if values else None


def key_accidental_count(key):
    """Number of sharps/flats in a key signature like 'G', 'F#m', 'Ddor'."""
    if not key:
        return 0
    m = re.match(r"([A-Ga-g])([#b]?)\s*([A-Za-z]*)", key)
    if not m:
        return 0
    tonic = m.group(1).upper() + m.group(2)
    mode = m.group(3).lower()[:3]
    if mode.startswith("m") and mode not in ("mix", "maj"):
        mode = "m"
    if tonic not in MAJOR_KEY_FIFTHS or mode not in MODE_OFFSET:
        return 0
    return abs(MAJOR_KEY_FIFTHS[tonic] + MODE_OFFSET[mode])


def music_body(abc):
    """The note-bearing part of an ABC tune: no headers, comments, chords symbols or annotations."""
    lines = [line for line in abc.split("\n") if line.strip() and not HEADER_LINE_RE.match(line)]
    body = "\n".join(lines)
    body = INLINE_FIELD_RE.sub(" ", body)
    body = QUOTED_RE.sub(" ", body)
    return body


def note_pitch(accidental, letter, octave_marks):
    pitch = 60 + BASE_SEMITONE[letter.upper()] + (12 if letter.islower() else 0)
    pitch += 12 * octave_marks.count("'") - 12 * octave_marks.count(",")
    pitch += {"^": 1, "^^": 2, "_": -1, "__": -2}.get(accidental or "", 0)
    return pitch


def difficulty_features(abc):
    """Numeric features of a melody, or None if it has no notes."""
    body = music_body(abc)
    ornaments = len(DECORATION_RE.findall(body)) + body.count("~")
    body = DECORATION_RE.sub(" ", body)

    notes = NOTE_RE.findall(body)
    if not notes:
        return None
    pitches = [note_pitch(acc, letter, octave) for acc, letter, octave, _ in notes]
    leaps = [abs(b - a) for a, b in zip(pitches, pitches[1:])]
    bars = max(body.count("|"), 1)

    tempo_text = header_value(abc, "Q")
    tempo_numbers = re.findall(r"\d+", tempo_text or "")
    tempo = int(tempo_numbers[-1]) if tempo_numbers else None

    return {
        "pitch_range": max(pitches) - min(pitches),
        "mean_leap": statistics.mean(leaps) if leaps else 0.0,
        "accidentals": sum(1 for acc, *_ in notes if acc) / len(notes),
        "key_accidentals": key_accidental_count(header_value(abc, "K")),
        "rhythm_variety": len({length for *_, length in notes}),
        "notes_per_bar": len(notes) / bars,
        "ornaments": ornaments / len(notes),
        "tempo": tempo,
    }


# -------------------------
# Records
# -------------------------
def record_task(record):
    if record.get("task"):
        return str(record["task"]).strip().lower()
    for line in (record.get("input") or "").split("\n"):
        m = TASK_LINE_RE.match(line.strip())
        if m and m.group(1).lower() not in ("input", "output"):
            return m.group(1).lower()
    return None


def clean_input(text):
    """Remove any difficulty tag left by an earlier run, in either format."""
    text = text or ""
    if not (OLD_TAG_RE.search(text) or DIFFICULTY_LINE_RE.search(text)):
        return text
    text = OLD_TAG_RE.sub("", text)
    return re.sub(r"\n{2,}", "\n", DIFFICULTY_LINE_RE.sub("", text))


def add_difficulty_line(input_text, difficulty):
    """Insert '%%difficulty=<level>' right after the task line (or at the start)."""
    tag = f"%%difficulty={difficulty}"
    lines = clean_input(input_text).split("\n")
    for i, line in enumerate(lines):
        m = TASK_LINE_RE.match(line.strip())
        if m and m.group(1).lower() not in ("input", "output", "difficulty"):
            return "\n".join(lines[: i + 1] + [tag] + lines[i + 1:])
    return tag + "\n" + "\n".join(lines)


def read_records(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


# -------------------------
# Calibration and scoring
# -------------------------
class DifficultyScale:
    """Standardises features and splits scores into easy / medium / hard thirds."""

    def __init__(self, feature_samples):
        self.stats = {}
        for name in WEIGHTS:
            values = [f[name] for f in feature_samples if f[name] is not None]
            mean = statistics.mean(values) if values else 0.0
            stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
            self.stats[name] = (mean, stdev or 1.0)
        scores = sorted(self.score(f) for f in feature_samples)
        if len(scores) >= 3:
            self.cutoffs = (scores[len(scores) // 3], scores[2 * len(scores) // 3])
        else:
            self.cutoffs = (0.0, 0.0)

    def score(self, features):
        total = 0.0
        for name, weight in WEIGHTS.items():
            mean, stdev = self.stats[name]
            value = features[name] if features[name] is not None else mean
            total += weight * (value - mean) / stdev
        return total

    def level(self, features):
        s = self.score(features)
        if s < self.cutoffs[0]:
            return "easy"
        if s < self.cutoffs[1]:
            return "medium"
        return "hard"


def calibrate(path, sample_size, seed=0):
    """Reservoir-sample melody features from the whole file (not just its start)."""
    rng = random.Random(seed)
    sample, seen = [], 0
    for record in read_records(path):
        if record_task(record) not in MELODY_TASKS:
            continue
        features = difficulty_features(record.get("output") or "")
        if features is None:
            continue
        seen += 1
        if len(sample) < sample_size:
            sample.append(features)
        else:
            j = rng.randrange(seen)
            if j < sample_size:
                sample[j] = features
    return DifficultyScale(sample)


def tag_file(input_path, output_path, scale):
    counts = defaultdict(Counter)
    with open(output_path, "w", encoding="utf-8") as out:
        for record in read_records(input_path):
            task = record_task(record)
            features = difficulty_features(record.get("output") or "") if task in MELODY_TASKS else None
            if features is None:
                record["input"] = clean_input(record.get("input"))
                counts[task]["untagged"] += 1
            else:
                level = scale.level(features)
                record["input"] = add_difficulty_line(record.get("input"), level)
                counts[task][level] += 1
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return counts


def print_summary(path, counts):
    print(f"\n{path}")
    print(f"  {'task':<15}{'easy':>9}{'medium':>9}{'hard':>9}{'untagged':>10}")
    for task in sorted(counts, key=str):
        c = counts[task]
        print(f"  {str(task):<15}{c['easy']:>9}{c['medium']:>9}{c['hard']:>9}{c['untagged']:>10}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", type=Path,
                        help="JSONL files; the first one is used for calibration")
    parser.add_argument("--sample-size", type=int, default=20000,
                        help="melodies sampled for calibration (default: 20000)")
    args = parser.parse_args()

    print(f"Calibrating on {args.inputs[0]} ...")
    scale = calibrate(args.inputs[0], args.sample_size)
    print(f"Cut-offs: easy < {scale.cutoffs[0]:.2f} <= medium < {scale.cutoffs[1]:.2f} <= hard")

    for input_path in args.inputs:
        output_path = input_path.with_name(input_path.stem + "_tagged.jsonl")
        print_summary(output_path, tag_file(input_path, output_path, scale))


if __name__ == "__main__":
    main()
