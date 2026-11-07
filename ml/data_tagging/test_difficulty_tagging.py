"""Run from the repository root: python -m unittest discover ml/data_tagging"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import difficulty_tagging as dt  # noqa: E402

MEDIUM = "X:1\nL:1/8\nM:4/4\nK:G\nG2 AB c2 BA | G2 d2 B2 G2 | ^F2 GA B2 AG | D8 |]\n"
EASY = "X:1\nL:1/4\nM:4/4\nK:C\nC D E F | G G G G | F E D C | C4 |]\n"
HARD = ("X:1\nL:1/16\nM:4/4\nQ:1/4=160\nK:C#m\n"
        "!trill!c'2^g^f e^dcB ^A,4 g'2 | _B,2 ~e'3/2 ^^f/ c'''8 a,,4 |\n")


def load_patchilizer():
    """MelodyT5's Patchilizer, without importing torch/transformers."""
    src = (Path(__file__).parents[1] / "melodyt5" / "utils.py").read_text()
    ns = {"re": re, "unidecode": lambda s: s, "PATCH_LENGTH": 256, "PATCH_SIZE": 64}
    exec(src[src.index("class Patchilizer"):src.index("class PatchLevelEnDecoder")], ns)
    return ns["Patchilizer"]()


class FeatureTests(unittest.TestCase):
    def test_ignores_headers_and_titles(self):
        with_title = "X:1\nT:A Grand Cafe Ballad\nL:1/4\nK:C\nC D E F |\n"
        without = "X:1\nL:1/4\nK:C\nC D E F |\n"
        self.assertEqual(dt.difficulty_features(with_title), dt.difficulty_features(without))

    def test_harder_melody_scores_higher(self):
        easy, hard = dt.difficulty_features(EASY), dt.difficulty_features(HARD)
        scale = dt.DifficultyScale([easy, hard, dt.difficulty_features(EASY.replace("C4", "c4"))])
        self.assertLess(scale.score(easy), scale.score(hard))
        self.assertGreater(hard["pitch_range"], easy["pitch_range"])
        self.assertGreater(hard["accidentals"], easy["accidentals"])
        self.assertEqual(hard["key_accidentals"], 4)  # C# minor
        self.assertEqual(hard["tempo"], 160)

    def test_no_notes(self):
        self.assertIsNone(dt.difficulty_features("S:2\nB:5\nE:4\n"))


class SegmentationTests(unittest.TestCase):
    # Real MelodyHub segmentation outputs mark phrases with !breath!.
    PLAIN = 'X:1\nL:1/4\nM:3/4\nK:C\n"C" c |"C" c2"G/B" g |"C" e3/2 d/"Am" c |"G" d2"C" e |\n'
    MARKED = 'X:1\nL:1/4\nM:3/4\nK:C\n"C" c |"C" c2"G/B" g |"C" e3/2 d/"Am" c |"G" !breath!d2"C" e |\n'

    def test_breath_marks_change_nothing(self):
        self.assertEqual(dt.difficulty_features(self.MARKED), dt.difficulty_features(self.PLAIN))
        self.assertEqual(dt.difficulty_features(self.MARKED)["ornaments"], 0)

    def test_real_ornaments_still_count(self):
        self.assertGreater(dt.difficulty_features(self.PLAIN.replace("d2", "!trill!d2"))["ornaments"], 0)


class TagFormatTests(unittest.TestCase):
    def test_tag_goes_after_task_line(self):
        self.assertEqual(dt.add_difficulty_line("%%generation\n", "easy"),
                         "%%generation\n%%difficulty=easy\n")
        self.assertEqual(dt.add_difficulty_line("%%input\n%%harmonization\nK:G\nGAB|\n", "hard"),
                         "%%input\n%%harmonization\n%%difficulty=hard\nK:G\nGAB|\n")

    def test_retagging_replaces_old_tags(self):
        old = "<difficulty=hard> %%generation\n"
        once = dt.add_difficulty_line(old, "easy")
        self.assertEqual(once, "%%generation\n%%difficulty=easy\n")
        self.assertEqual(dt.add_difficulty_line(once, "medium"), "%%generation\n%%difficulty=medium\n")

    def test_model_encoder_keeps_the_tag(self):
        p = load_patchilizer()
        bars = [p.patch2bar(x) for x in p.encode(dt.add_difficulty_line("%%generation\n", "easy"))]
        self.assertEqual(bars, ["%%generation\n", "%%difficulty=easy\n"])


class FileTests(unittest.TestCase):
    def test_tags_melody_tasks_only(self):
        records = [{"task": "generation", "input": "%%generation\n", "output": tune}
                   for tune in (EASY, MEDIUM, HARD) for _ in range(5)] + [
            {"task": "cataloging", "input": "%%cataloging\n" + EASY, "output": "S:2\nB:4\n"}]
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, "train.jsonl")
            src.write_text("".join(json.dumps(r) + "\n" for r in records))
            dst = Path(d, "train_tagged.jsonl")
            counts = dt.tag_file(src, dst, dt.calibrate(src, 100))
            tagged = [json.loads(line) for line in dst.read_text().splitlines()]

        self.assertEqual(counts["cataloging"]["untagged"], 1)
        self.assertEqual(tagged[-1]["input"], records[-1]["input"])
        self.assertIn("%%difficulty=easy", tagged[0]["input"])
        self.assertIn("%%difficulty=medium", tagged[5]["input"])
        self.assertIn("%%difficulty=hard", tagged[10]["input"])
        self.assertEqual([r["output"] for r in tagged], [r["output"] for r in records])


if __name__ == "__main__":
    unittest.main()
