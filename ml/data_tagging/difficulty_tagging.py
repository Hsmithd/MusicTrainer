import json
import re
import argparse
import numpy as np


# -------------------------
# Feature extraction
# -------------------------
def difficulty_features(abc_string):
    s = str(abc_string or "")

    # Remove the unwanted B: and S: tags along with %%book and %%source
    s = re.sub(r"%%\s*(book|source)", "", s)
    s = re.sub(r"^B:.*$", "", s, flags=re.MULTILINE)  # Remove B: line
    s = re.sub(r"^S:.*$", "", s, flags=re.MULTILINE)  # Remove S: line

    unique_pitches = len(set(re.findall(r"[A-Ga-g]", s)))
    unique_rhythms = len(set(re.findall(r"\d+", s)))
    accidentals = s.count('^') + s.count('_')
    ornaments = len(re.findall(r"[~HLMOPSTuv]", s))
    note_count = len(re.findall(r"[A-Ga-g]", s))

    tempo_match = re.search(r"Q:\s*(\d+)", s)
    tempo = int(tempo_match.group(1)) if tempo_match else 100

    return {
        "unique_pitches": unique_pitches,
        "unique_rhythms": unique_rhythms,
        "accidentals": accidentals,
        "ornaments": ornaments,
        "note_count": note_count,
        "tempo": tempo
    }


# -------------------------
# Scoring
# -------------------------
DEFAULT_WEIGHTS = {
    "unique_pitches": 1.5,
    "unique_rhythms": 1.2,
    "accidentals": 1.3,
    "ornaments": 1.5,
    "note_count": 0.01,
    "tempo": 0.02
}


def calibrated_difficulty_score(abc_string, weights):
    feats = difficulty_features(abc_string)
    tempo_factor = max(feats["tempo"] - 60, 0)
    return (
            feats["unique_pitches"] * weights["unique_pitches"] +
            feats["unique_rhythms"] * weights["unique_rhythms"] +
            feats["accidentals"] * weights["accidentals"] +
            feats["ornaments"] * weights["ornaments"] +
            feats["note_count"] * weights["note_count"] +
            tempo_factor * weights["tempo"]
    )


# -------------------------
# Helpers: detect ABC presence & tags
# -------------------------
DIFFICULTY_RE = re.compile(r"<\s*difficulty\s*=\s*(easy|medium|hard)\s*>", flags=re.I)
ABC_PRESENCE_RE = re.compile(r"[A-Ga-g]|T:|K:|L:|M:")  # simple heuristic


def has_difficulty_tag(s):
    return bool(s and DIFFICULTY_RE.search(s))


def contains_abc(s):
    return bool(s and ABC_PRESENCE_RE.search(s))


# -------------------------
# Combine input/output scores
# -------------------------
def combine_scores(score_in, score_out, method="max", w_in=0.5, w_out=0.5):
    # score_in/out can be None
    if score_in is None and score_out is None:
        return None
    if score_in is None:
        return score_out
    if score_out is None:
        return score_in

    if method == "max":
        return max(score_in, score_out)
    elif method == "avg":
        return 0.5 * (score_in + score_out)
    elif method == "weighted":
        total = w_in + w_out
        if total == 0:
            return 0.5 * (score_in + score_out)
        return (w_in * score_in + w_out * score_out) / total
    else:
        # fallback to max
        return max(score_in, score_out)


# -------------------------
# Auto-calibration (first pass streaming)
# -------------------------
def auto_calibrate_from_file(input_path, sample_limit=2000, weights=DEFAULT_WEIGHTS,
                             combine_method="max", w_in=0.5, w_out=0.5):
    scores = []
    seen = 0
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue

            inp = rec.get("input", "") or ""
            out = rec.get("output", "") or ""

            # compute per-side scores only if ABC-like content exists on that side
            s_in = None
            s_out = None
            try:
                if contains_abc(inp):
                    s_in = calibrated_difficulty_score(inp, weights)
                if contains_abc(out):
                    s_out = calibrated_difficulty_score(out, weights)
            except Exception:
                pass

            combined = combine_scores(s_in, s_out, method=combine_method, w_in=w_in, w_out=w_out)
            if combined is not None:
                scores.append(combined)

            seen += 1
            if sample_limit and len(scores) >= sample_limit:
                break

    if not scores:
        # fallback thresholds
        return weights, (10.0, 30.0)

    arr = np.array(scores)
    easy = float(np.percentile(arr, 33))
    medium = float(np.percentile(arr, 66))
    return weights, (easy, medium)


# -------------------------
# Difficulty tag selection
# -------------------------
def get_difficulty_tag(score, thresholds):
    if score is None:
        # default to medium when no score
        return "<difficulty=medium>"
    if score <= thresholds[0]:
        return "<difficulty=easy>"
    elif score <= thresholds[1]:
        return "<difficulty=medium>"
    else:
        return "<difficulty=hard>"


# -------------------------
# Infer task (preserve if present)
# -------------------------
def infer_task(record, output_text):
    if record.get("task"):
        return str(record["task"])
    for candidate in ("type", "label"):
        if candidate in record and record[candidate]:
            return str(record[candidate])
    s = (output_text or "") + "\n" + (record.get("input") or "")
    if re.search(r"%%\s*generation", s, flags=re.I) or "%%generation" in s:
        return "generation"
    if re.search(r"%%\s*cataloging", s, flags=re.I) or "%%cataloging" in s:
        return "cataloging"
    if re.search(r"%%\s*segmentation", s, flags=re.I) or "%%segmentation" in s:
        return "segmentation"
    return "cataloging"


# -------------------------
# Transform: second pass writes tagged JSONL
# -------------------------
def transform_file(input_path, output_path, sample_calib=2000, combine_method="max",
                   w_in=0.5, w_out=0.5, dataset_name_default="ABC Notation"):
    print(f"Auto-calibrating from {input_path} (sampling up to {sample_calib}) ...")
    weights, thresholds = auto_calibrate_from_file(input_path, sample_limit=sample_calib,
                                                   weights=DEFAULT_WEIGHTS,
                                                   combine_method=combine_method,
                                                   w_in=w_in, w_out=w_out)
    print(f"Calibration done. thresholds: easy <= {thresholds[0]:.4f}, medium <= {thresholds[1]:.4f}")

    total = 0
    written = 0
    with open(input_path, "r", encoding="utf-8") as fi, open(output_path, "w", encoding="utf-8") as fo:
        for line in fi:
            total += 1
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue

            # ensure dataset exists
            if not rec.get("dataset"):
                rec["dataset"] = dataset_name_default

            # preserve or infer task
            task_val = rec.get("task") if rec.get("task") else infer_task(rec, rec.get("output", ""))
            rec["task"] = task_val

            input_text = rec.get("input", "") or ""
            output_text = rec.get("output", "") or ""

            # If input already has difficulty tag, keep it exactly
            if has_difficulty_tag(input_text):
                new_input = input_text
            else:
                # compute per-side scores if ABC-like content exists
                s_in = None
                s_out = None
                try:
                    if contains_abc(input_text):
                        s_in = calibrated_difficulty_score(input_text, weights)
                    if contains_abc(output_text):
                        s_out = calibrated_difficulty_score(output_text, weights)
                except Exception:
                    s_in = s_in or None
                    s_out = s_out or None

                combined = combine_scores(s_in, s_out, method=combine_method, w_in=w_in, w_out=w_out)

                # fallback if no combined score
                if combined is None:
                    # choose medium by default
                    tag = "<difficulty=medium>"
                else:
                    tag = get_difficulty_tag(combined, thresholds)

                if str(input_text).strip() == "":
                    new_input = f"{tag} "
                else:
                    new_input = f"{tag} {input_text}"

            # preserve output exactly
            rec["input"] = new_input
            rec["output"] = output_text

            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    print(f"Finished. Processed {total} lines, wrote {written} records to {output_path}")


# -------------------------
# CLI
# -------------------------
def main():
    p = argparse.ArgumentParser(description="Tag JSONL records using difficulty computed from input+output.")
    p.add_argument("--input", "-i", default="train.jsonl", help="input JSONL path")
    p.add_argument("--output", "-o", default="train_tagged.jsonl", help="output JSONL path")
    p.add_argument("--sample-calib", type=int, default=2000, help="how many combined scores to sample for calibration")
    p.add_argument("--combine-method", choices=("max", "avg", "weighted"), default="max",
                   help="how to combine input/output scores into a single difficulty score (default: max)")
    p.add_argument("--w-input", type=float, default=0.5, help="weight for input when --combine-method weighted")
    p.add_argument("--w-output", type=float, default=0.5, help="weight for output when --combine-method weighted")
    p.add_argument("--dataset-name", default="ABC Notation", help="default dataset name if missing")
    args = p.parse_args()

    transform_file(args.input, args.output, sample_calib=args.sample_calib,
                   combine_method=args.combine_method, w_in=args.w_input, w_out=args.w_output,
                   dataset_name_default=args.dataset_name)


if __name__ == "__main__":
    main()
