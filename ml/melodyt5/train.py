import os
import time
import json
from array import array
import torch
import random
import numpy as np
from copy import deepcopy
from utils import *
from config import *
from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader, RandomSampler
from transformers import GPT2Config, get_constant_schedule_with_warmup
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler

# -------------------------
# Distributed / Device Setup
# -------------------------
world_size = int(os.environ.get('WORLD_SIZE', 1))
global_rank = int(os.environ.get('RANK', 0))
local_rank = int(os.environ.get('LOCAL_RANK', 0))

# Use a GPU when there is one (e.g. the cluster via training.sh), otherwise the CPU.
use_cuda = torch.cuda.is_available()
if use_cuda:
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)
else:
    device = torch.device("cpu")

if world_size > 1:
    os.environ['USE_LIBUV'] = '0'  # Disable libuv on Windows
    dist.init_process_group(backend='nccl' if use_cuda else 'gloo', init_method='env://')
    print(f"[Rank {global_rank}] Distributed training enabled (world size={world_size}, device={device})")
else:
    print(f"Single-process mode (device={device})")

# -------------------------
# Reproducibility
# -------------------------
seed = 42 + global_rank
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# -------------------------
# Model, Patchilizer, Optimizer
# -------------------------
batch_size = BATCH_SIZE
patchilizer = Patchilizer()

patch_config = GPT2Config(num_hidden_layers=PATCH_NUM_LAYERS,
                          max_length=PATCH_LENGTH,
                          max_position_embeddings=PATCH_LENGTH,
                          vocab_size=1)
char_config = GPT2Config(num_hidden_layers=CHAR_NUM_LAYERS,
                         max_length=PATCH_SIZE,
                         max_position_embeddings=PATCH_SIZE,
                         vocab_size=128)

model = MelodyT5(patch_config, char_config).to(device)
print("Parameter Number:", sum(p.numel() for p in model.parameters() if p.requires_grad))

if world_size > 1:
    model = DDP(model, device_ids=[local_rank] if use_cuda else None, find_unused_parameters=True)

optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

# -------------------------
# Dataset / DataLoader
# -------------------------
def collate_batch(batch):
    input_patches, input_masks, output_patches, output_masks = [], [], [], []

    for input_patch, output_patch in batch:
        input_patches.append(input_patch)
        input_masks.append(torch.tensor([1]*input_patch.shape[0]))
        output_patches.append(output_patch)
        output_masks.append(torch.tensor([1]*output_patch.shape[0]))

    input_patches = torch.nn.utils.rnn.pad_sequence(input_patches, batch_first=True, padding_value=0)
    input_masks = torch.nn.utils.rnn.pad_sequence(input_masks, batch_first=True, padding_value=0)
    output_patches = torch.nn.utils.rnn.pad_sequence(output_patches, batch_first=True, padding_value=0)
    output_masks = torch.nn.utils.rnn.pad_sequence(output_masks, batch_first=True, padding_value=0)

    return input_patches.to(device), input_masks.to(device), output_patches.to(device), output_masks.to(device)

class MelodyHubDataset(Dataset):
    """Reads examples from a JSONL file on demand, so memory use stays small.

    Only the byte offset of each line is kept in memory (8 bytes per example);
    each example is read and encoded when the DataLoader asks for it.
    """
    def __init__(self, path):
        self.path = path
        self.offsets = array('q')
        with open(path, 'rb') as f:
            position = 0
            for line in f:
                if line.strip():
                    self.offsets.append(position)
                position += len(line)
        self.file = None

    def __len__(self):
        return len(self.offsets)

    def __getitem__(self, idx):
        if self.file is None:
            self.file = open(self.path, 'rb')
        self.file.seek(self.offsets[idx])
        item = json.loads(self.file.readline())
        input_patch = torch.tensor(patchilizer.encode(item['input'], add_special_patches=True))
        output_patch = torch.tensor(patchilizer.encode(item['output'], add_special_patches=True))
        return input_patch, output_patch

# -------------------------
# Training / Evaluation
# -------------------------
def process_one_batch(batch):
    input_patches, input_masks, output_patches, output_masks = batch
    loss = model(input_patches, input_masks, output_patches, output_masks)
    if world_size > 1:
        loss = loss.unsqueeze(0)
        dist.reduce(loss, dst=0)
        loss = loss / world_size
        dist.broadcast(loss, src=0)
    return loss

def train_epoch():
    tqdm_train_set = tqdm(train_loader)
    total_train_loss, iter_idx = 0, 1
    model.train()
    for batch in tqdm_train_set:
        loss = process_one_batch(batch)
        if loss is None or torch.isnan(loss).item():
            continue
        loss.backward()
        optimizer.step()
        lr_scheduler.step()
        model.zero_grad(set_to_none=True)
        total_train_loss += loss.item()
        tqdm_train_set.set_postfix({str(global_rank)+'_train_loss': total_train_loss/iter_idx})
        iter_idx += 1
    return total_train_loss/(iter_idx-1)

def eval_epoch():
    tqdm_eval_set = tqdm(eval_loader)
    total_eval_loss, iter_idx = 0, 1
    model.eval()
    for batch in tqdm_eval_set:
        with torch.no_grad():
            loss = process_one_batch(batch)
        if loss is None or torch.isnan(loss).item():
            continue
        total_eval_loss += loss.item()
        tqdm_eval_set.set_postfix({str(global_rank)+'_eval_loss': total_eval_loss/iter_idx})
        iter_idx += 1
    return total_eval_loss/(iter_idx-1)

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    # Data is read from disk as needed (see MelodyHubDataset), not loaded into memory.
    train_set = MelodyHubDataset(TRAIN_DATA_PATH)
    eval_set = MelodyHubDataset(VALIDATION_DATA_PATH)
    print(f"Training examples: {len(train_set)}, validation examples: {len(eval_set)}")

    if world_size > 1:
        train_sampler = DistributedSampler(train_set, num_replicas=world_size, rank=local_rank)
        eval_sampler = DistributedSampler(eval_set, num_replicas=world_size, rank=local_rank)
    else:
        # Each epoch trains on a fresh random subset of TRAIN_SAMPLES_PER_EPOCH examples
        # (or everything if it's None), so an epoch takes a predictable amount of time.
        num_samples = min(TRAIN_SAMPLES_PER_EPOCH or len(train_set), len(train_set))
        train_sampler = RandomSampler(train_set, num_samples=num_samples)
        eval_sampler = None
        print(f"Examples per epoch: {num_samples}")

    train_loader = DataLoader(train_set, batch_size=batch_size, collate_fn=collate_batch,
                              sampler=train_sampler, drop_last=True)
    eval_loader = DataLoader(eval_set, batch_size=batch_size, collate_fn=collate_batch,
                             sampler=eval_sampler, drop_last=True)

    lr_scheduler = get_constant_schedule_with_warmup(optimizer=optimizer, num_warmup_steps=1000)

    # Load pretrained / checkpoint if needed
    pre_epoch, best_epoch, min_eval_loss = 0, 0, float('inf')
    if LOAD_FROM_PRETRAINED and os.path.exists(PRETRAINED_PATH):
        checkpoint = torch.load(PRETRAINED_PATH, map_location='cpu')
        if world_size > 1 and hasattr(model, 'module'):
            cpu_model = deepcopy(model.module)
            cpu_model.load_state_dict(checkpoint['model'])
            model.module.load_state_dict(cpu_model.state_dict())
        else:
            cpu_model = deepcopy(model)
            cpu_model.load_state_dict(checkpoint['model'])
            model.load_state_dict(cpu_model.state_dict())
        print(f"Loaded pretrained weights from {PRETRAINED_PATH}")
    elif LOAD_FROM_PRETRAINED:
        raise FileNotFoundError(f"{PRETRAINED_PATH} not found. Download the MelodyT5 weights first (see README).")

    if LOAD_FROM_CHECKPOINT and os.path.exists(WEIGHTS_PATH):
        checkpoint = torch.load(WEIGHTS_PATH, map_location='cpu')
        if world_size > 1 and hasattr(model, 'module'):
            cpu_model = deepcopy(model.module)
            cpu_model.load_state_dict(checkpoint['model'])
            model.module.load_state_dict(cpu_model.state_dict())
        else:
            cpu_model = deepcopy(model)
            cpu_model.load_state_dict(checkpoint['model'])
            model.load_state_dict(cpu_model.state_dict())
        optimizer.load_state_dict(checkpoint['optimizer'])
        lr_scheduler.load_state_dict(checkpoint['lr_sched'])
        pre_epoch = checkpoint['epoch']
        best_epoch = checkpoint['best_epoch']
        min_eval_loss = checkpoint['min_eval_loss']
        print(f"Loaded checkpoint from epoch {pre_epoch}")

    # Training loop
    for epoch in range(pre_epoch+1, NUM_EPOCHS+1):
        if world_size > 1:
            train_sampler.set_epoch(epoch)
            eval_sampler.set_epoch(epoch)
        print('-'*21 + f" Epoch {epoch} " + '-'*21)

        train_loss = train_epoch()
        eval_loss = eval_epoch()

        if global_rank == 0:
            with open(LOGS_PATH,'a') as f:
                f.write(f"Epoch {epoch}\ntrain_loss: {train_loss}\neval_loss: {eval_loss}\ntime: {time.asctime()}\n\n")
            if eval_loss < min_eval_loss:
                best_epoch = epoch
                min_eval_loss = eval_loss
                checkpoint = {
                    'model': model.module.state_dict() if hasattr(model, 'module') else model.state_dict(),
                    'optimizer': optimizer.state_dict(),
                    'lr_sched': lr_scheduler.state_dict(),
                    'epoch': epoch,
                    'best_epoch': best_epoch,
                    'min_eval_loss': min_eval_loss
                }
                torch.save(checkpoint, WEIGHTS_PATH)

        if world_size > 1: dist.barrier()

    if global_rank == 0:
        print("Best Eval Epoch:", best_epoch)
        print("Min Eval Loss:", min_eval_loss)