"""Check whether the fine-tuned model follows the requested difficulty.

Generates tunes at each difficulty (and once with no difficulty, as a
baseline), scores them with the same measure used to tag the training data,
and prints how they compare. Run from ml/melodyt5:

    python evaluate_difficulty.py
    python evaluate_difficulty.py -n 20     # more tunes per level, more reliable

If the model learned the tags, the average score should rise from easy to
medium to hard, and most tunes should land in the level that was asked for.
"""
import argparse
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data_tagging"))
import difficulty_tagging as dt  # noqa: E402

# Same sampling settings the app uses (backend/trainer/services/etude_service.py)
INFERENCE_ARGS = ["-max_patch", "128", "-top_p", "0.8", "-top_k", "8",
                  "-temperature", "2.6", "-show_control_code", "True"]


def generate(n, difficulty, output_path):
    command = [sys.executable, "inference.py", "-num_tunes", str(n), "-output", str(output_path), *INFERENCE_ARGS]
    if difficulty:
        command += ["-difficulty", difficulty]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"inference.py failed:\n{result.stderr}")
    if difficulty and "ignored" in result.stdout:
        sys.exit("inference.py ignored -difficulty: weights_difficulty.pth wasn't found.")
    return [t for t in Path(output_path).read_text().split("\n\n") if t.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-n", type=int, default=10, help="tunes per difficulty (default: 10)")
    parser.add_argument("-calibration", default="../data/melodyhub/validation.jsonl",
                        help="data used to set the easy/medium/hard cut-offs")
    args = parser.parse_args()

    print(f"Calibrating difficulty scale on {args.calibration} ...")
    scale = dt.calibrate(args.calibration, sample_size=20000)

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for requested in (None, "easy", "medium", "hard"):
            label = requested or "(none)"
            print(f"Generating {args.n} tunes, difficulty {label} ...", flush=True)
            tunes = generate(args.n, requested, os.path.join(tmp, f"{label}.abc"))
            features = [f for f in (dt.difficulty_features(t) for t in tunes) if f]
            scores = [scale.score(f) for f in features]
            levels = [scale.level(f) for f in features]
            rows.append((label, len(tunes), scores, levels))

    print(f"\n{'requested':<10}{'tunes':>6}{'avg score':>11}{'easy':>7}{'medium':>8}{'hard':>7}")
    for label, count, scores, levels in rows:
        avg = f"{statistics.mean(scores):.2f}" if scores else "-"
        pct = {lvl: f"{100 * levels.count(lvl) / len(levels):.0f}%" if levels else "-" for lvl in dt.DIFFICULTIES}
        print(f"{label:<10}{count:>6}{avg:>11}{pct['easy']:>7}{pct['medium']:>8}{pct['hard']:>7}")
    print("\nWorking: the average score rises from easy to medium to hard, and each row's")
    print("largest share is the level that was requested. Scores are noisy with few tunes;")
    print("use -n 20 or more before drawing conclusions.")


if __name__ == "__main__":
    main()
