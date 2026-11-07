# ML

- `melodyt5/` – the MelodyT5 model: inference (used by the backend) and training
- `data_tagging/` – adds difficulty tags to training data
- `notebooks/` – experiments
- `data/` – training data, **not in git** (download it as below)

## Getting the training data

The model is trained on [MelodyHub](https://huggingface.co/datasets/sander-wood/melodyhub)
(several GB). From the repository root:

```bash
python -m pip install -U huggingface_hub
```

```bash
hf download sander-wood/melodyhub --repo-type dataset --local-dir ml/data/melodyhub
```

`config.py` expects the tagged files at `ml/data/melodyhub/train_tagged.jsonl`
and `ml/data/melodyhub/validation_tagged.jsonl`.
