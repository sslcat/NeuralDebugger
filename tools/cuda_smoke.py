"""Check a real Qwen query projection and LoRA gradient in a small GPU footprint."""

import json
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from safetensors import safe_open
from neuraldebugger.model import location
from neuraldebugger.settings import TRAINING as C


class Projection(torch.nn.Module):
    def __init__(self, weights):
        super().__init__()
        self.q_proj = torch.nn.Linear(
            weights.shape[1],
            weights.shape[0],
            bias=False,
            device="cuda",
            dtype=weights.dtype,
        )
        with torch.no_grad():
            self.q_proj.weight.copy_(weights)

    def forward(self, x):
        return self.q_proj(x)


def run():
    if not torch.cuda.is_available() or torch.cuda.mem_get_info()[0] < 300 * 2**20:
        raise RuntimeError("Insufficient free CUDA memory for this probe")
    torch.manual_seed(C["seed"])
    torch.cuda.reset_peak_memory_stats()
    with safe_open(str(Path(location()) / "model.safetensors"), framework="pt") as f:
        weight = f.get_tensor("model.layers.0.self_attn.q_proj.weight")
    model = get_peft_model(
        Projection(weight),
        LoraConfig(r=C["rank"], lora_alpha=C["alpha"], target_modules=["q_proj"]),
    )
    x = torch.randn(1, 16, weight.shape[1], device="cuda", dtype=weight.dtype)
    opt = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=C["learning_rate"]
    )
    loss = model(x).float().square().mean()
    loss.backward()
    assert any(
        p.grad is not None and p.grad.abs().max().item() > 0
        for p in model.parameters()
        if p.requires_grad
    )
    opt.step()
    torch.cuda.synchronize()
    print(
        json.dumps(
            dict(
                probe="single frozen query projection and LoRA backward",
                gpu=torch.cuda.get_device_name(),
                peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                dtype=str(weight.dtype),
                passed=True,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
