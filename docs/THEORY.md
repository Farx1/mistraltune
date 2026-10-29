# Theory: LoRA, QLoRA and VRAM

What `src/train_qlora.py` does, and how to estimate whether a run fits on a GPU.
Notation: a linear layer `y = W0 x` with `W0` of shape `d × k` (output × input), LoRA rank `r ≪ min(d, k)`.

## 1. LoRA

Source: Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models*, 2021, [arXiv:2106.09685](https://arxiv.org/abs/2106.09685), §4.1.

LoRA freezes `W0` and learns a low-rank update:

```
h = W0 x + ΔW x = W0 x + (α / r) · B A x        B: d × r,  A: r × k
```

- **Initialization.** `A` is random Gaussian, `B = 0`, so `ΔW = BA = 0` at step 0: training starts exactly from the base model.
- **Scaling.** `ΔW x` is scaled by `α / r` (`lora_alpha / lora_r` in `configs/lora_*.yaml`). Keeping `α / r` fixed (8/16, 16/32, 32/64 here: ratio 2) means changing `r` does not require retuning the learning rate as much.
- **Parameter count.** A full update of `W0` trains `d·k` values; LoRA trains `r·(d + k)`. For a square layer (`d = k`) that is `2dr` instead of `d²`, i.e. a ratio of `2r/d`. For `d = 4096`, `r = 16`: 131 072 vs 16 777 216, 0.78 %.
- **Merge is exact.** After training, `W = W0 + (α/r)·BA` is a plain `d × k` matrix. The merged model computes the same function with no extra latency (§4.1). `tests/test_lora_tiny.py` (#8) checks this numerically on a tiny model.

### Trainable parameters for Mistral-7B (this repo's configs)

Mistral-7B: 32 layers, hidden 4096, KV dim 1024 (8 KV heads × 128), MLP 14 336.
Per layer, `r·(d + k)` summed over the targeted projections:

| Module | `k → d` | `d + k` |
|--------|---------|---------|
| q_proj, o_proj | 4096 → 4096 | 8 192 each |
| k_proj, v_proj | 4096 → 1024 | 5 120 each |
| gate_proj, up_proj | 4096 → 14 336 | 18 432 each |
| down_proj | 14 336 → 4096 | 18 432 |
| **all 7** | | **81 920** |

Trainable parameters = `32 × 81 920 × r`:

| Config | Target modules | r | Trainable params |
|--------|----------------|---|------------------|
| `lora_r8a16.yaml` | all 7 | 8 | 21.0 M |
| `lora_r16a32.yaml` | all 7 | 16 | 41.9 M |
| `lora_r32a64.yaml` | all 7 | 32 | 83.9 M |
| `sample_lora.yaml` | q, k, v, o | 8 | 6.8 M |

Check the target modules of each file before quoting a number; `get_peft_model(...).print_trainable_parameters()` prints the real count.

## 2. QLoRA

Source: Dettmers et al., *QLoRA: Efficient Finetuning of Quantized LLMs*, 2023, [arXiv:2305.14314](https://arxiv.org/abs/2305.14314), §3.

QLoRA keeps LoRA but stores the frozen `W0` in 4 bits:

```
Y(bf16) = X(bf16) · doubleDequant(c1(fp32), c2(k-bit), W(NF4)) + X(bf16) · L1(bf16) · L2(bf16)
```

- **Storage vs compute dtype.** Weights are stored as 4-bit NormalFloat and dequantized to 16 bits only for the matmul. Gradients flow through the frozen weights to the LoRA matrices `L1, L2` (= `B, A`) only.
- **NF4 (4-bit NormalFloat).** Pretrained weights are roughly normally distributed. NF4 places its 16 levels at quantiles of N(0, 1), so each bin holds the same expected number of values. It also has an exact zero.
- **Blockwise quantization.** Weights are quantized in blocks of 64, each with its own scale (absmax). With fp32 scales that costs `32 / 64 = 0.5` extra bits per parameter.
- **Double quantization.** The scales themselves are quantized to 8-bit floats in blocks of 256. Overhead drops to `8/64 + 32/(64·256) ≈ 0.127` bits per parameter, a saving of 0.373 bits per parameter (about 3 GB on a 65B model, §1).
- **Paged optimizers.** Optimizer states move to CPU RAM on memory spikes (not used by `train_qlora.py`).

In this repo: `create_bnb_config()` in `src/train_qlora.py` sets `bnb_4bit_quant_type="nf4"` and `bnb_4bit_use_double_quant=True`. The compute dtype is fp16 (`fp16: true` in `configs/base.yaml`), not bf16 as in the paper, so it also runs on GPUs without bf16.

## 3. VRAM estimate

Training memory is roughly the sum of four terms (`P` = base parameters, `P_L` = LoRA parameters):

```
VRAM ≈ P × (4 + 0.127) / 8           # frozen weights, NF4 + double-quant constants   (bytes)
     + P_L × (4 + 4 + 8)             # LoRA weights fp32 + gradients fp32 + Adam m and v fp32
     + activations                   # grows with batch × seq_len × hidden × layers
     + ~0.5-1 GB                     # CUDA context, allocator fragmentation
```

- LoRA weights are fp32: `get_peft_model()` defaults to `autocast_adapter_dtype=True` (peft 0.12). AdamW keeps two fp32 moments per trainable parameter.
- Frozen weights get no gradient and no optimizer state: that is the whole saving versus full fine-tuning (`P × 16` bytes with fp32 Adam).
- Activations dominate at long sequence lengths. `prepare_model_for_kbit_training()` enables gradient checkpointing by default, which stores roughly one `batch × seq_len × hidden` tensor per layer and recomputes the rest in the backward pass.

Worked example, Mistral-7B (`P ≈ 7.24 B`), `lora_r16a32.yaml` (`P_L = 41.9 M`), batch 1, seq 2048:

| Term | Estimate |
|------|----------|
| NF4 weights + constants | 7.24e9 × 4.127 / 8 ≈ 3.7 GB |
| LoRA weights + grads + Adam | 41.9e6 × 16 B ≈ 0.67 GB |
| Checkpointed layer inputs (fp16) | 32 × 1 × 2048 × 4096 × 2 B ≈ 0.54 GB |
| One layer recomputed + logits + overhead | a few GB, measure it |

This is a floor, not a promise: the embedding and LM head are usually not quantized, and the logits tensor (`seq_len × 32 768` vocab) alone is ~0.27 GB in fp32 per sequence. The only reliable number is `torch.cuda.max_memory_allocated()` from a real run; record it in `MODEL_CARD.md` once measured.
