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

## Fine-tuning for difficulty

`ml/melodyt5/config.py` is set up to fine-tune: it starts from the original
weights (`weights.pth`, never overwritten) and saves the best epoch to
`weights_difficulty.pth`. It uses a GPU when one is available.

1. Put `weights.pth` in `ml/melodyt5/` and the tagged data in `ml/data/melodyhub/`.
2. From `ml/melodyt5/`, train on one GPU with `python train.py`, or on the
   cluster with `sbatch training.sh` (2 GPUs).
3. Copy `weights_difficulty.pth` back into `ml/melodyt5/` on the machine
   running the app.

Training reads examples from disk as it goes, so it doesn't need much memory.
On one GPU each epoch uses `TRAIN_SAMPLES_PER_EPOCH` random examples (100,000
by default, different each epoch); set it to `None` to use all ~1.4 million.
Watch the time estimate on the progress bar and adjust it or `NUM_EPOCHS`.

GPU memory is set by `config.py`:

- `PATCH_SAMPLING_BATCH_SIZE` (128): bars per batch the note-level decoder
  trains on. The biggest lever, roughly 20 MB per bar.
- `BATCH_SIZE` (5) with `ACCUMULATION_STEPS` (2): tunes per batch on the GPU,
  and how many batches are combined per update (10 tunes per update).

If the GPU runs out of memory, lower `PATCH_SAMPLING_BATCH_SIZE` first.

`weights_difficulty.pth` is about 2 GB because it also stores the optimizer
state. If training stops partway, set `LOAD_FROM_CHECKPOINT = True` to resume.

## How the app uses it

The difficulty slider sends `easy`/`medium`/`hard` to `/api/generate-etude/`,
and the backend runs:

```bash
python inference.py -difficulty easy -output output_tunes/etude_<id>.abc ...
```

`inference.py` loads `weights_difficulty.pth` if it exists and adds
`%%difficulty=<level>` to the prompt, the same as the tagged training data.
Until that file exists it uses `weights.pth` and ignores the difficulty, since
the original model was never taught the tag.
