from __future__ import annotations

from functools import lru_cache
import os
from typing import Any


class QwenUnavailableError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _load_model():
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:  # pragma: no cover - dependency failure path
        raise QwenUnavailableError(
            "Qwen generation requires torch and transformers. Install the backend requirements first."
        ) from exc

    model_name = os.getenv("QWEN_MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")
    device = os.getenv("QWEN_DEVICE", "cpu")
    dtype_name = os.getenv("QWEN_DTYPE", "auto")

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model_kwargs: dict[str, Any] = {"trust_remote_code": True}
    if dtype_name != "auto":
        dtype = getattr(torch, dtype_name, None)
        if dtype is not None:
            model_kwargs["torch_dtype"] = dtype

    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    if device != "auto":
        model = model.to(device)

    return tokenizer, model


def generate_with_qwen(payload: dict[str, Any]) -> str:
    from .analyst import build_analyst_prompt

    prompt = build_analyst_prompt(payload)
    tokenizer, model = _load_model()

    messages = [
        {
            "role": "system",
            "content": "You are a precise, evidence-driven football tactical analyst.",
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    try:
        chat_prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        chat_prompt = prompt

    inputs = tokenizer(chat_prompt, return_tensors="pt")
    input_device = getattr(model, "device", None)
    if input_device is not None:
        inputs = {key: value.to(input_device) for key, value in inputs.items()}

    max_new_tokens = int(os.getenv("QWEN_MAX_NEW_TOKENS", "320"))
    temperature = float(os.getenv("QWEN_TEMPERATURE", "0.3"))
    top_p = float(os.getenv("QWEN_TOP_P", "0.9"))

    import torch

    with torch.no_grad():
        generated = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=float(os.getenv("QWEN_REPETITION_PENALTY", "1.05")),
        )

    prompt_length = inputs["input_ids"].shape[-1]
    output_ids = generated[0][prompt_length:]
    text = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
    return text
