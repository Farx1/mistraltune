# Model Card for Mistral-7B-Instruct QLoRA Domain QA

## Model Details

### Model Description
This model is a fine-tuned version of Mistral-7B-Instruct-v0.3 using QLoRA (Quantized Low-Rank Adaptation) for domain-specific question-answering tasks in French and English. The model has been trained on a curated dataset of business and technology-related questions and answers.

- **Base Model**: mistralai/Mistral-7B-Instruct-v0.3
- **Fine-tuning Method**: QLoRA (4-bit quantization + LoRA adapters)
- **Task**: Question Answering (Domain-specific)
- **Languages**: French, English
- **Model Size**: ~7B parameters (base) + LoRA adapters (~16M parameters)

### Model Architecture
- **Architecture**: Transformer-based causal language model
- **Quantization**: 4-bit (NF4) with double quantization
- **LoRA Configuration**: 
  - Target modules: q_proj, v_proj, k_proj, o_proj, gate_proj, up_proj, down_proj
  - Rank (r): 8, 16, or 32 (depending on variant)
  - Alpha: 16, 32, or 64 (depending on variant)
  - Dropout: 0.05

## Training

### Training Data
- **Training Set**: 20 examples of domain-specific Q&A pairs
- **Validation Set**: 5 examples
- **Test Set**: 5 examples
- **Domain**: Business, technology, SaaS, startup terminology
- **Languages**: Mixed French and English
- **Format**: Instruction-following format with structured prompts

### Training Procedure
- **Framework**: PyTorch 2.x, Transformers, TRL, PEFT
- **Quantization**: BitsAndBytesConfig with 4-bit NF4
- **Optimizer**: AdamW
- **Learning Rate**: 1e-4
- **Batch Size**: 1 (per device) with gradient accumulation of 8
- **Epochs**: 3
- **Sequence Length**: 2048 tokens
- **Packing**: Enabled for efficient training
- **Mixed Precision**: FP16

### Training Infrastructure
- **Hardware**: Single GPU (24-48 GB VRAM recommended)
- **Training Time**: ~10-30 minutes per variant
- **Peak VRAM Usage**: ~12-16 GB (depending on LoRA rank)
- **Reproducibility**: Fixed random seed (42)

## Evaluation

### Evaluation Metrics
- **Exact Match (EM)**: Percentage of exactly correct answers
- **F1 Score**: Token-level F1 score based on overlap
- **Latency**: Inference time (p50, p95 percentiles)
- **VRAM Usage**: Peak memory consumption during inference

### Evaluation Methodology
- **Evaluation Set**: 5 validation examples
- **Inference**: Greedy decoding (deterministic)
- **Max New Tokens**: 128
- **Latency Measurement**: 50 runs per model
- **Hardware**: Same as training (single GPU)

### Results Summary
| Model Variant | EM Score | F1 Score | Latency p50 | Latency p95 | VRAM (GB) |
|---------------|----------|----------|-------------|-------------|-----------|
| Baseline | 0.XXX | 0.XXX | X.XXXs | X.XXXs | ~XX |
| LoRA r8/a16 | 0.XXX | 0.XXX | X.XXXs | X.XXXs | ~XX |
| LoRA r16/a32 | 0.XXX | 0.XXX | X.XXXs | X.XXXs | ~XX |
| LoRA r32/a64 | 0.XXX | 0.XXX | X.XXXs | X.XXXs | ~XX |

*Note: Results will be populated after training and evaluation*

## Usage

### Loading the Model
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.3",
    torch_dtype=torch.float16,
    device_map="auto"
)

# Load LoRA adapter
model = PeftModel.from_pretrained(base_model, "path/to/adapter")

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3")
```

### Inference Example
```python
def generate_answer(instruction, input_text=""):
    if input_text:
        prompt = f"{instruction}\n{input_text}"
    else:
        prompt = instruction
    
    formatted_prompt = f"<s>[INST] {prompt} [/INST]"
    
    inputs = tokenizer(formatted_prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        max_new_tokens=128,
        do_sample=False,
        temperature=0.7,
        top_p=0.9
    )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.split("[/INST]")[1].strip()

# Example usage
answer = generate_answer("What is SaaS?")
print(answer)
```

## Limitations

### Known Limitations
- **Small Dataset**: Training on only 20 examples limits generalization
- **Domain Specificity**: Optimized for business/tech terminology
- **Language Mix**: Primarily English with some French examples
- **Context Length**: Limited to 2048 tokens
- **Hallucinations**: May generate plausible but incorrect information

### Potential Risks
- **Overfitting**: High risk due to small dataset size
- **Bias**: Inherits biases from base model and training data
- **Misinformation**: May generate incorrect domain-specific information
- **Language Quality**: Mixed language training may affect fluency

## Ethical Considerations

### Intended Use
- Educational purposes and research
- Domain-specific question answering
- Business and technology terminology assistance
- Demonstration of QLoRA fine-tuning techniques

### Misuse Prevention
- **Content Filtering**: Basic safety checks implemented
- **PII Protection**: Training data does not contain personal information
- **Bias Monitoring**: Regular evaluation on diverse test cases
- **Transparency**: Open-source implementation and documentation

### Recommendations
- Use with human oversight for critical decisions
- Verify important information from authoritative sources
- Consider domain-specific fine-tuning for production use
- Implement additional safety measures for sensitive applications

## Technical Specifications

### Hardware Requirements
- **Training**: GPU with 24-48 GB VRAM
- **Inference**: GPU with 8-16 GB VRAM (with quantization)
- **CPU**: Multi-core processor recommended
- **RAM**: 32+ GB system memory

### Software Dependencies
- Python 3.10+
- PyTorch 2.2+
- Transformers 4.44+
- PEFT 0.12+
- BitsAndBytes 0.43+
- CUDA 11.8+ (for GPU acceleration)

### Model Files
- **Base Model**: Downloaded from HuggingFace Hub
- **LoRA Adapters**: Stored in `runs/` directory
- **Tokenizer**: Shared with base model
- **Config**: YAML configuration files

## Citation

```bibtex
@software{mistral7b_qlora_domainqa,
  title={Mistral-7B QLoRA Domain QA},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/mistral7b-qlora-domainqa},
  license={MIT}
}
```

## License

This model is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For questions, issues, or contributions, please open an issue on the project repository or contact the maintainer.

---

**Model Card Version**: 1.0  
**Last Updated**: 2024-10-14  
**Maintainer**: Your Name
