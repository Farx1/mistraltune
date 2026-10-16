"""
LoRA mechanics on a tiny random Mistral, CPU only (no bitsandbytes).

Same checks as the PEFT/TRL test suites: loss goes down, the adapter round-trips
through save/load, and merging W0 + (alpha/r)·BA gives the same forward pass.

Run: pytest -m slow tests/test_lora_tiny.py   (needs requirements-train.txt, downloads ~2 MB)
"""

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("peft")
pytest.importorskip("transformers")

from peft import LoraConfig, PeftModel, get_peft_model  # noqa: E402
from transformers import AutoModelForCausalLM  # noqa: E402

pytestmark = pytest.mark.slow

MODEL = "hf-internal-testing/tiny-random-MistralForCausalLM"


def test_lora_train_save_load_merge(tmp_path):
    torch.manual_seed(0)
    model = get_peft_model(
        AutoModelForCausalLM.from_pretrained(MODEL),
        LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, task_type="CAUSAL_LM",
                   target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]),
    )
    ids = torch.randint(0, model.config.vocab_size, (2, 16))

    # B = 0 at init: the adapter starts as an exact no-op
    model.eval()
    with torch.no_grad():
        with model.disable_adapter():
            base_logits = model(input_ids=ids).logits
        torch.testing.assert_close(model(input_ids=ids).logits, base_logits)

    # Only LoRA matrices train
    assert all(("lora_" in n) == p.requires_grad for n, p in model.named_parameters())

    # Loss goes down on a fixed batch
    model.train()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-2)
    losses = []
    for _ in range(10):
        loss = model(input_ids=ids, labels=ids).loss
        loss.backward()
        opt.step()
        opt.zero_grad()
        losses.append(loss.item())
    assert losses[-1] < losses[0], losses

    model.eval()
    with torch.no_grad():
        ref = model(input_ids=ids).logits
    assert not torch.allclose(ref, base_logits)  # training changed something

    # Save/load round-trip of the adapter alone
    model.save_pretrained(tmp_path)
    reloaded = PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(MODEL), tmp_path).eval()
    with torch.no_grad():
        torch.testing.assert_close(reloaded(input_ids=ids).logits, ref)

    # Merge: W = W0 + (alpha/r)·B·A, checked on one layer, then on the full forward pass
    q = model.base_model.model.model.layers[0].self_attn.q_proj
    expected_w = q.base_layer.weight + q.scaling["default"] * q.lora_B["default"].weight @ q.lora_A["default"].weight
    expected_w = expected_w.detach().clone()
    merged = model.merge_and_unload()
    torch.testing.assert_close(merged.model.layers[0].self_attn.q_proj.weight, expected_w)
    with torch.no_grad():
        torch.testing.assert_close(merged(input_ids=ids).logits, ref, rtol=1e-4, atol=1e-4)
