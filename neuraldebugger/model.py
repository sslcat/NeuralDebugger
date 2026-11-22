import json
import os
from .weights import base_directory, load_adapter

from .settings import PROTOCOL, REV

def messages(code, traceback):
    return [{"role": "system", "content": PROTOCOL["system"]},
            {"role": "user", "content": json.dumps({"code": code, "observed_failure": traceback}, ensure_ascii=False)}]

def location():
    return base_directory()

def choose_device():
    import torch
    choice = os.getenv("ND_DEVICE", "auto")
    if choice not in {"auto", "cuda", "cpu"}:
        raise ValueError("ND_DEVICE must be auto, cuda or cpu")
    if choice != "auto":
        return choice
    return "cuda" if torch.cuda.is_available() and torch.cuda.mem_get_info()[0] > 4.5 * 2**30 else "cpu"

class Engine:
    def __init__(self, adapter=None, strict=False):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.device = choose_device()
        torch.set_num_threads(int(os.getenv("ND_CPU_THREADS", "6")))
        self.dtype = torch.bfloat16 if self.device == "cpu" or torch.cuda.is_bf16_supported() else torch.float16
        source = location()
        self.tok = AutoTokenizer.from_pretrained(source, revision=REV, local_files_only=True, trust_remote_code=False)
        def base():
            return AutoModelForCausalLM.from_pretrained(source, revision=REV, torch_dtype=self.dtype,
                local_files_only=True, trust_remote_code=False, use_safetensors=True, device_map={"": self.device}, attn_implementation="sdpa").eval()
        self.model = base()
        self.mode = "base"
        self.warning = None
        if adapter:
            try:
                self.model = load_adapter(self.model, adapter)
                self.mode = "adapter"
            except Exception:
                if strict:
                    raise
                del self.model
                self.model = base()
                self.warning = "Adapter could not load. The base model is active."

    def predict(self, code, traceback):
        import torch
        prompt = self.tok.apply_chat_template(messages(code, traceback), tokenize=True, add_generation_prompt=True)
        if len(prompt) > PROTOCOL["max_input_tokens"]:
            raise OverflowError("Input exceeds the 1536-token context budget.")
        x = torch.tensor([prompt], device=self.device)
        with torch.inference_mode():
            output = self.model.generate(input_ids=x, attention_mask=torch.ones_like(x),
                max_new_tokens=PROTOCOL["max_new_tokens"], do_sample=False, num_beams=1,
                pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(output[0, x.shape[1]:], skip_special_tokens=True)

