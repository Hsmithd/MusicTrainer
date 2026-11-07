# ML

- `melodyt5/` – the MelodyT5 model: inference (used by the backend) and training
- `data_tagging/` – adds difficulty tags to training data
- `notebooks/` – experiments
- `data/` – training data, **not in git** (download it as below)

## Getting the training data

The model is trained on [MelodyHub](https://huggingface.co/datasets/sander-wood/melodyhub)
(several GB). From the repository root (the version pin keeps `huggingface_hub`
compatible with `transformers`):

```bash
python -m pip install "huggingface_hub>=0.34,<1.0"
```

```bash
hf download sander-wood/melodyhub --repo-type dataset --local-dir ml/data/melodyhub
```

`config.py` expects the tagged files at `ml/data/melodyhub/train_tagged.jsonl`
and `ml/data/melodyhub/validation_tagged.jsonl`.

## Tagging the data with difficulty

```bash
python ml/data_tagging/difficulty_tagging.py ml/data/melodyhub/train.jsonl ml/data/melodyhub/validation.jsonl
```

This writes `train_tagged.jsonl` and `validation_tagged.jsonl` next to the
originals and prints how many records of each task got each level. Each
melody record gets a control line after its task line:

```
%%generation
%%difficulty=easy
```

Difficulty is scored from the output melody's notes (range, leaps,
accidentals, key signature, rhythmic variety, note density, ornaments,
tempo) and split into thirds. Cataloging records are left untagged because
their output isn't a melody. Running it again replaces existing tags.

Tests (no torch needed):

```bash
python -m unittest discover ml/data_tagging
```
