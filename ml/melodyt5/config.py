PATCH_LENGTH = 256      # Patch Length
PATCH_SIZE = 64       # Patch Size

PATCH_NUM_LAYERS = 9         # Number of layers in the encoder
CHAR_NUM_LAYERS = 3          # Number of layers in the decoder

NUM_EPOCHS = 10                # Fine-tuning epochs (the best epoch by validation loss is kept)
LEARNING_RATE = 1e-4           # Lower than pre-training (2e-4) so fine-tuning doesn't undo what the model knows
ACCUMULATION_STEPS = 2          # Batches whose gradients are combined per update (effective batch = BATCH_SIZE * this)
BATCH_SIZE = 5                 # Tunes per batch on the GPU; lower it if you run out of GPU memory
TRAIN_SAMPLES_PER_EPOCH = 100_000  # Random examples per epoch on one GPU (None = all ~1.4M); different each epoch
PATCH_SAMPLING_BATCH_SIZE = 128  # Max bars per batch the note-level decoder trains on (random subset). Biggest GPU-memory lever: ~20 MB per bar. 0 = all
LOAD_FROM_CHECKPOINT = False     # Resume an interrupted fine-tuning run from WEIGHTS_PATH
LOAD_FROM_PRETRAINED = True     # Start from the pretrained MelodyT5 weights (fine-tuning, not training from scratch)
SHARE_WEIGHTS = False            # Whether to share weights between the encoder and decoder

# Paths are relative to ml/melodyt5 (where train.py runs). Data is not in git;
# see ml/README.md for how to download and tag it.
TRAIN_DATA_PATH      = '../data/melodyhub/train_tagged.jsonl'
VALIDATION_DATA_PATH = '../data/melodyhub/validation_tagged.jsonl'

PRETRAINED_PATH = "weights.pth"             # Original MelodyT5 weights (download; never overwritten)
WEIGHTS_PATH = "weights_difficulty.pth"     # Fine-tuned weights that understand %%difficulty=easy/medium/hard
LOGS_PATH = "logs.txt"          # Path to save the logs