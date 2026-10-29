"""Mistral SDK call shape (mocked client, no network)."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mistral_api_finetune import create_finetuning_job, upload_dataset


def test_create_job_uses_sdk_1x_kwargs():
    client = Mock()
    client.fine_tuning.jobs.create.return_value = Mock(id="j", status="QUEUED", model="m", created_at=0)

    create_finetuning_job(client, "open-mistral-7b", "file-t", "file-v",
                          learning_rate=2e-4, epochs=2, batch_size=8, suffix="qa")

    client.fine_tuning.jobs.create.assert_called_once_with(
        model="open-mistral-7b",
        hyperparameters={"learning_rate": 2e-4, "epochs": 2},
        training_files=[{"file_id": "file-t", "weight": 1}],
        validation_files=["file-v"],
        suffix="qa",
        invalid_sample_skip_percentage=0,
    )


def test_upload_converts_instruction_output_to_messages(tmp_path):
    src = tmp_path / "train.jsonl"
    src.write_text(
        '{"instruction": "Translate", "input": "Hello", "output": "Bonjour"}\n'
        '{"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Yo"}]}\n',
        encoding="utf-8",
    )
    client = Mock()
    client.files.upload.return_value = Mock(id="file-1")

    assert upload_dataset(client, str(src)) == "file-1"

    sent = client.files.upload.call_args.kwargs["file"]
    rows = [json.loads(l) for l in sent["content"].decode("utf-8").splitlines()]
    assert sent["file_name"] == "train.jsonl"
    assert rows[0] == {"messages": [
        {"role": "user", "content": "Translate\n\nHello"},
        {"role": "assistant", "content": "Bonjour"},
    ]}
    assert rows[1]["messages"][1]["content"] == "Yo"
