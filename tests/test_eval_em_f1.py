"""EM/F1 on known cases, and the eval script must at least parse (it did not)."""

from pathlib import Path

import pytest

pytest.importorskip("sklearn")  # utils.metrics imports it

from utils.metrics import compute_metrics  # noqa: E402


def test_eval_script_parses():
    src = Path(__file__).parent.parent / "src" / "eval_em_f1.py"
    compile(src.read_text(encoding="utf-8"), str(src), "exec")


def test_compute_metrics_known_cases():
    # exact after normalization / 2 of 3 tokens shared / no answer
    em, f1 = compute_metrics(["Paris.", "the cat sat", ""], ["paris", "the dog sat", "x"])
    assert em == pytest.approx(1 / 3)
    assert f1 == pytest.approx((1 + 2 / 3 + 0) / 3)


def test_compute_metrics_length_mismatch():
    with pytest.raises(ValueError):
        compute_metrics(["a"], [])
