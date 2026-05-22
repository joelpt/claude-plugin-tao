"""
Model registry for tao multi-LLM consensus.
Reference documentation only — not imported by llm_call.py.

Verified against live /models endpoints: 2026-05-22.
"""

MODELS = {
    # xAI Grok — adversarial critic voice
    "xai/grok-4.3": {
        "provider": "xai",
        "model_id": "grok-4.3",
        "context_window": 256_000,
        "role": "critic",
        "key_env": "XAI_API_KEY",
        "notes": "Sharp reasoning, adversarial framing. Ideal for devil's-advocate challenge mode.",
    },
    # OpenAI Codex CLI — neutral analyst voice (uses subscription quota, no per-token cost)
    "codex/default": {
        "provider": "codex",
        "model_id": None,
        "context_window": None,
        "role": "analyst",
        "key_env": None,
        "notes": "Routes through Codex CLI companion. Uses OpenAI subscription quota.",
        "setup": "claude plugin install codex@openai-codex",
    },
    # Google Gemini 2.5 Pro — available but not used in default config (per-token cost)
    "gemini/gemini-2.5-pro": {
        "provider": "gemini",
        "model_id": "gemini-2.5-pro",
        "context_window": 1_048_576,
        "role": "analyst-alt",
        "key_env": "GEMINI_API_KEY",
        "notes": "Available via --provider=gemini. Per-token cost. 1M context window.",
    },
    # Ollama local — independent local voice (free, no network)
    "ollama/qwen3:32b": {
        "provider": "ollama",
        "model_id": "qwen3:32b",
        "context_window": 32_768,
        "role": "local",
        "key_env": None,
        "notes": "~20GB, 18-25 t/s on M1 Max 64GB. Independent of all cloud providers.",
        "setup": "ollama pull qwen3:32b",
    },
}
