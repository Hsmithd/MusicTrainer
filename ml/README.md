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
