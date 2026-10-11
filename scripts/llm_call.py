#!/usr/bin/env python3
"""Multi-provider LLM caller for tao consensus/challenge modes.

Reads prompt from stdin, writes response to stdout.

Usage (explicit provider):
  echo "prompt" | python3 llm_call.py --provider=<gemini|xai|openai|groq|ollama|lmstudio|codex> [--model=<name>]
      [--system=<text>] [--max-tokens=<int>]

Usage (config-based role):
  echo "prompt" | python3 llm_call.py --config=<path/to/models.json> --role=<section.role>
      [--system=<text>] [--max-tokens=<int>]
  # --provider and --model override config values when provided alongside --role

API keys (from ~/.zshenv — never hardcoded):
  GEMINI_API_KEY  — Google Gemini (generativelanguage API v1beta)
  XAI_API_KEY     — xAI Grok (OpenAI-compatible endpoint at api.x.ai)
  OPENAI_API_KEY  — OpenAI direct (api.openai.com). Default model: gpt-5.
  GROQ_API_KEY    — Groq LPU inference (api.groq.com). Default model: meta-llama/llama-4-scout-17b-16e-instruct.
  (Codex uses the OpenAI Codex CLI companion — no key var needed here)
  (Ollama needs no key — local endpoint at localhost:11434)
  (LM Studio needs no key — OpenAI-compatible endpoint; URL from LMSTUDIO_BASE_URL, else the port in
   ~/.lmstudio/.internal/http-server-config.json, else 1234. A model is required: `lms ls` lists keys.
   LMSTUDIO_TTL (default 600 s idle unload), LMSTUDIO_TIMEOUT, LMSTUDIO_TEMPERATURE and
   LMSTUDIO_REASONING_EFFORT (default none = thinking off; none|minimal|low|medium|high|default) are optional.)
"""

import argparse
import http.client
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _version_key(v: str) -> tuple[int, ...]:
    """Return a numeric tuple for semver-safe sorting of version directory names.

    Args:
        v: Version string such as "1.2.3" or "v2.0.1-beta".

    Returns:
        Tuple of integers extracted from the version string, suitable for
        comparison with the builtin `sorted` key parameter.
    """
    return tuple(int(x) for x in re.split(r"[.\-]", v.lstrip("v")) if x.isdigit())


def _urlopen(
    req: urllib.request.Request,
    timeout: int,
    _retries: list[int] | None = None,
) -> http.client.HTTPResponse:
    """Open a URL request, retrying up to 8 times on 429/529 with exponential backoff.

    Args:
        req: The request to open.
        timeout: Socket timeout in seconds.
        _retries: If provided, the number of retries performed is appended on success.

    Returns:
        The HTTP response object from the successful request.
    """
    for attempt in range(9):
        try:
            response = urllib.request.urlopen(req, timeout=timeout)  # type: ignore[return-value]
            if _retries is not None:
                _retries.append(attempt)
            return response
        except urllib.error.HTTPError as e:
            # 529 = Anthropic overloaded; 429 = rate-limited (OpenAI, xAI, Gemini, most APIs).
            if e.code in (429, 529) and attempt < 8:
                delay = min(2**attempt + random.uniform(0, 1), 60)
                print(
                    f"[HTTP {e.code}] retrying in {delay:.1f}s (attempt {attempt + 1}/8)…",
                    file=sys.stderr,
                )
                time.sleep(delay)
            else:
                raise
    raise RuntimeError("unreachable")


def _emit_stats(
    provider: str,
    model: str,
    tok_in: int | str,
    tok_out: int | str,
    elapsed: float,
    tok_per_s: float | str,
    retries: int = 0,
) -> None:
    """Print a machine-parseable stats line to stderr for tao run summaries.

    Args:
        provider: Provider name (gemini, xai, openai, groq, ollama, lmstudio, codex).
        model: Model identifier string.
        tok_in: Input token count, or "?" if unavailable.
        tok_out: Output token count, or "?" if unavailable.
        elapsed: Wall-clock seconds including any 529 retry backoff.
        tok_per_s: Throughput, or "?" / "n/a" if unavailable.
        retries: Number of 529 retries performed; omitted from output when 0.
    """
    retry_suffix = f" retries={retries}" if retries > 0 else ""
    print(
        f"[tao-stats] provider={provider} model={model}"
        f" tok_in={tok_in} tok_out={tok_out}"
        f" elapsed={elapsed:.1f}s tok/s={tok_per_s if isinstance(tok_per_s, str) else f'{tok_per_s:.1f}'}"
        f"{retry_suffix}",
        file=sys.stderr,
    )


def call_gemini(prompt: str, model: str | None, system: str | None, max_tokens: int) -> str:
    """Call Google Gemini generateContent API and return the response text.

    Args:
        prompt: User message to send.
        model: Gemini model identifier; defaults to "gemini-2.5-pro".
        system: Optional system instruction text.
        max_tokens: Maximum output tokens to request.

    Returns:
        The text content from the first candidate's first part.
    """
    model = model or "gemini-2.5-pro"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body: dict[str, object] = {
        "contents": [{"parts": [{"text": prompt}], "role": "user"}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    _retries: list[int] = []
    t0 = time.monotonic()
    with _urlopen(req, timeout=120, _retries=_retries) as resp:
        result = json.loads(resp.read())
    elapsed = time.monotonic() - t0

    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates in Gemini response: {result}")
    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts")
    if not parts:
        finish = candidate.get("finishReason", "UNKNOWN")
        raise RuntimeError(
            f"Gemini returned no content (finishReason={finish}). "
            "Increase --max-tokens for thinking models."
        )
    text = parts[0].get("text")
    if text is None:
        raise RuntimeError(f"Gemini first part has no 'text' key (part type: {list(parts[0].keys())})")

    meta = result.get("usageMetadata", {})
    tok_in = meta.get("promptTokenCount", "?")
    tok_out = meta.get("candidatesTokenCount", "?")
    tok_per_s: float | str = tok_out / elapsed if isinstance(tok_out, int) and elapsed > 0 else "?"
    _emit_stats("gemini", model, tok_in, tok_out, elapsed, tok_per_s, retries=_retries[0] if _retries else 0)
    return text


def call_xai(prompt: str, model: str | None, system: str | None, max_tokens: int) -> str:
    """Call the xAI OpenAI-compatible API and return the response message content.

    Args:
        prompt: User message to send.
        model: xAI model identifier; defaults to "grok-4.3".
        system: Optional system prompt text.
        max_tokens: Maximum output tokens to request.

    Returns:
        The content string from the first response choice.
    """
    model = model or "grok-4.3"
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise RuntimeError("XAI_API_KEY not set in environment")

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body: dict[str, object] = {"model": model, "messages": messages, "max_tokens": max_tokens}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        "https://api.x.ai/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    _retries: list[int] = []
    t0 = time.monotonic()
    with _urlopen(req, timeout=120, _retries=_retries) as resp:
        result = json.loads(resp.read())
    elapsed = time.monotonic() - t0

    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError(f"xAI returned no choices (full response: {result})")
    content: str | None = choices[0]["message"].get("content")
    if content is None:
        finish = choices[0].get("finish_reason", "UNKNOWN")
        raise RuntimeError(f"xAI returned null content (finish_reason={finish})")
    usage = result.get("usage") or {}
    tok_in = usage.get("prompt_tokens", "?")
    tok_out = usage.get("completion_tokens", "?")
    tok_per_s: float | str = tok_out / elapsed if isinstance(tok_out, int) and elapsed > 0 else "?"
    _emit_stats("xai", model, tok_in, tok_out, elapsed, tok_per_s, retries=_retries[0] if _retries else 0)
    return content


def call_openai(prompt: str, model: str | None, system: str | None, max_tokens: int) -> str:
    """Call the OpenAI chat completions API and return the response message content.

    Args:
        prompt: User message to send.
        model: OpenAI model identifier; defaults to "gpt-5".
        system: Optional system prompt text.
        max_tokens: Maximum output tokens to request.

    Returns:
        The content string from the first response choice.
    """
    model = model or "gpt-5"
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    # max_completion_tokens is required for o-series and gpt-5+ (max_tokens is rejected).
    body: dict[str, object] = {"model": model, "messages": messages, "max_completion_tokens": max_tokens}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    _retries: list[int] = []
    t0 = time.monotonic()
    with _urlopen(req, timeout=120, _retries=_retries) as resp:
        result = json.loads(resp.read())
    elapsed = time.monotonic() - t0

    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError(f"OpenAI returned no choices (full response: {result})")
    content: str | None = choices[0]["message"].get("content")
    if content is None:
        finish = choices[0].get("finish_reason", "UNKNOWN")
        raise RuntimeError(f"OpenAI returned null content (finish_reason={finish})")
    usage = result.get("usage") or {}
    tok_in = usage.get("prompt_tokens", "?")
    tok_out = usage.get("completion_tokens", "?")
    tok_per_s: float | str = tok_out / elapsed if isinstance(tok_out, int) and elapsed > 0 else "?"
    _emit_stats("openai", model, tok_in, tok_out, elapsed, tok_per_s, retries=_retries[0] if _retries else 0)
    return content


def call_groq(prompt: str, model: str | None, system: str | None, max_tokens: int) -> str:
    """Call the Groq LPU inference API and return the response message content.

    Args:
        prompt: User message to send.
        model: Groq model identifier; defaults to "meta-llama/llama-4-scout-17b-16e-instruct".
        system: Optional system prompt text.
        max_tokens: Maximum output tokens to request.

    Returns:
        The content string from the first response choice.
    """
    model = model or "meta-llama/llama-4-scout-17b-16e-instruct"
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body: dict[str, object] = {"model": model, "messages": messages, "max_tokens": max_tokens}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    _retries: list[int] = []
    t0 = time.monotonic()
    with _urlopen(req, timeout=120, _retries=_retries) as resp:
        result = json.loads(resp.read())
    elapsed = time.monotonic() - t0

    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError(f"Groq returned no choices (full response: {result})")
    content: str | None = choices[0]["message"].get("content")
    if content is None:
        finish = choices[0].get("finish_reason", "UNKNOWN")
        raise RuntimeError(f"Groq returned null content (finish_reason={finish})")
    usage = result.get("usage") or {}
    tok_in = usage.get("prompt_tokens", "?")
    tok_out = usage.get("completion_tokens", "?")
    tok_per_s: float | str = tok_out / elapsed if isinstance(tok_out, int) and elapsed > 0 else "?"
    _emit_stats("groq", model, tok_in, tok_out, elapsed, tok_per_s, retries=_retries[0] if _retries else 0)
    return content


def _estimate_tokens(text: str) -> int:
    """Return a rough token count (about 4 characters per token).

    Used only for pre-flight sizing and warnings; real counts come from the server's usage report.

    Args:
        text: The text to size.

    Returns:
        An estimated token count, at least 1.
    """
    return max(1, len(text) // 4)


def _ollama_num_ctx(required_tokens: int) -> int:
    """Return the context window to request from Ollama for a prompt plus its output budget.

    Args:
        required_tokens: Estimated prompt tokens plus the output token budget.

    Returns:
        A multiple of 2048 between 16384 and 131072 that covers the requirement with headroom.
    """
    padded = required_tokens + 512
    rounded = -(-padded // 2048) * 2048
    return min(131072, max(16384, rounded))


def call_ollama(prompt: str, model: str | None, system: str | None, max_tokens: int) -> str:
    """Call the local Ollama /api/chat endpoint and return the assistant message content.

    Args:
        prompt: User message to send.
        model: Ollama model identifier; defaults to "qwen3:32b".
        system: Optional system prompt text.
        max_tokens: Maximum output tokens for the response (thinking overhead added automatically).

    Returns:
        The assistant message content, or thinking content if content is empty.
    """
    model = model or "qwen3:32b"
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    _THINKING_MODELS = {"qwen3", "deepseek-r1"}
    thinking = any(model.startswith(prefix) for prefix in _THINKING_MODELS)

    # Thinking tokens consume from the same num_predict budget as content tokens.
    # Add a fixed 8192-token thinking overhead so CoT doesn't crowd out the response.
    num_predict = max_tokens + 8192 if thinking else max_tokens

    # Ollama silently truncates a prompt that exceeds the context it was loaded with, so size it explicitly.
    num_ctx = _ollama_num_ctx(_estimate_tokens((system or "") + prompt) + num_predict)

    body: dict[str, object] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": thinking,
        "keep_alive": "10m",
        "options": {"num_predict": num_predict, "num_ctx": num_ctx},
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    # Generous timeout — first call may load the model from disk
    _retries: list[int] = []
    t0 = time.monotonic()
    try:
        with _urlopen(req, timeout=300, _retries=_retries) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        # HTTPError is a URLError subclass: it must be handled first, or a 404 (model not pulled)
        # is misreported as "server not reachable".
        detail = e.read().decode(errors="replace")[:500]
        if e.code == 404:
            raise RuntimeError(
                f"Ollama has no model '{model}' (HTTP 404: {detail}). Run: ollama pull {model}"
            ) from e
        raise RuntimeError(f"Ollama HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Ollama not reachable at localhost:11434 ({e.reason}). "
            "Run: ollama serve"
        ) from e
    elapsed = time.monotonic() - t0

    error_msg = result.get("error")
    if error_msg:
        raise RuntimeError(f"Ollama error: {error_msg}")
    msg = result.get("message", {})
    content = msg.get("content")
    if not content:
        if msg.get("thinking"):
            raise RuntimeError(
                "Ollama returned only reasoning, no answer "
                f"(done_reason={result.get('done_reason', 'unknown')}). The token budget ran out while thinking: "
                "raise --max-tokens or use a non-thinking model."
            )
        raise RuntimeError(f"Ollama returned no message content (response: {result})")

    tok_in = result.get("prompt_eval_count", "?")
    if isinstance(tok_in, int) and tok_in >= num_ctx - 64:
        raise RuntimeError(
            f"Ollama counted {tok_in} prompt tokens against a {num_ctx}-token context: the input was truncated, "
            "so the review would cover a partial prompt."
        )
    tok_out = result.get("eval_count", "?")
    # Use Ollama's native eval_duration (nanoseconds) for accurate GPU throughput.
    eval_ns = result.get("eval_duration")
    if isinstance(tok_out, int) and isinstance(eval_ns, int) and eval_ns > 0:
        tok_per_s: float | str = tok_out / (eval_ns / 1e9)
    elif isinstance(tok_out, int) and elapsed > 0:
        tok_per_s = tok_out / elapsed
    else:
        tok_per_s = "?"
    _emit_stats("ollama", model, tok_in, tok_out, elapsed, tok_per_s, retries=_retries[0] if _retries else 0)
    return content


#: Idle seconds before LM Studio unloads a model that this provider JIT-loaded (override: LMSTUDIO_TTL).
LMSTUDIO_DEFAULT_TTL_SECONDS = 600
#: Extra output tokens granted so a thinking model's reasoning cannot crowd out the answer (only when thinking is on).
LMSTUDIO_THINKING_OVERHEAD = 8192
#: Thinking is off by default: measured on an M1 Max, a 27B dense model generates ~9 tokens/s, so unbounded
#: reasoning on a plan-sized prompt overran a 570 s timeout. Override: LMSTUDIO_REASONING_EFFORT
#: (none | minimal | low | medium | high | default, where default omits the parameter).
LMSTUDIO_DEFAULT_REASONING_EFFORT = "none"
#: Socket read timeout; stays under the 600 s Bash-tool timeout the vet references set (override: LMSTUDIO_TIMEOUT).
LMSTUDIO_TIMEOUT_SECONDS = 570
_LMSTUDIO_SERVER_CONFIG = Path.home() / ".lmstudio" / ".internal" / "http-server-config.json"


def _lmstudio_base_url(config_path: Path | None = None) -> str:
    """Return LM Studio's OpenAI-compatible base URL (ending in /v1, no trailing slash).

    Resolution order: ``LMSTUDIO_BASE_URL``, then the port in LM Studio's own server config, then 1234.

    Args:
        config_path: Override for the server config location (tests).

    Returns:
        The base URL.
    """
    env = os.environ.get("LMSTUDIO_BASE_URL")
    if env:
        return env.rstrip("/")
    port = 1234
    try:
        raw = json.loads((config_path or _LMSTUDIO_SERVER_CONFIG).read_text(encoding="utf-8"))
        port = int(raw.get("port", port))
    except (OSError, ValueError, AttributeError):
        pass
    return f"http://127.0.0.1:{port}/v1"


def _lmstudio_loaded_context(base_url: str, model: str) -> int | None:
    """Return the context length of *model*'s loaded instance, or None if it is not loaded or unknown.

    Args:
        base_url: The OpenAI-compatible base URL (ending in /v1).
        model: The model key.

    Returns:
        The smallest loaded context length, or None.
    """
    root = base_url[: -len("/v1")] if base_url.endswith("/v1") else base_url
    try:
        with _urlopen(urllib.request.Request(f"{root}/api/v1/models"), timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, OSError, ValueError):
        return None
    for entry in data.get("models", []):
        if entry.get("key") != model:
            continue
        lengths = [
            inst.get("config", {}).get("context_length")
            for inst in entry.get("loaded_instances", [])
        ]
        ints = [n for n in lengths if isinstance(n, int)]
        return min(ints) if ints else None
    return None


def call_lmstudio(prompt: str, model: str | None, system: str | None, max_tokens: int) -> str:
    """Call LM Studio's OpenAI-compatible chat endpoint and return the answer text.

    The request carries a per-request ``ttl`` so the model unloads after it has been idle that long.
    That only applies to models LM Studio JIT-loads: one loaded by hand never unloads, and the context
    length cannot be set per request, so it is checked instead (before and after the call).

    Args:
        prompt: User message to send.
        model: LM Studio model key (see ``lms ls``); required.
        system: Optional system prompt text.
        max_tokens: Maximum answer tokens (a thinking allowance is added automatically).

    Returns:
        The assistant's answer text.
    """
    if not model:
        raise RuntimeError(
            "LM Studio: no model configured. Set this role's model key in config/models.json "
            "(list installed models with: lms ls)."
        )
    base = _lmstudio_base_url()
    ttl = int(os.environ.get("LMSTUDIO_TTL", LMSTUDIO_DEFAULT_TTL_SECONDS))
    effort = os.environ.get("LMSTUDIO_REASONING_EFFORT", LMSTUDIO_DEFAULT_REASONING_EFFORT)
    # Thinking tokens come out of the same max_tokens budget, so allow for them unless thinking is off.
    budget = max_tokens if effort == "none" else max_tokens + LMSTUDIO_THINKING_OVERHEAD
    full_text = (system or "") + prompt

    loaded_ctx = _lmstudio_loaded_context(base, model)
    if loaded_ctx is not None:
        # len/6 is a floor on the token count (very sparse text), so tripping it means the input cannot fit.
        if len(full_text) // 6 >= loaded_ctx - 256:
            raise RuntimeError(
                f"LM Studio: the input (about {len(full_text) // 4} tokens) cannot fit the loaded context window "
                f"of {loaded_ctx} tokens. Raise this model's context length in LM Studio's model settings "
                "(loading it by hand with `lms load` disables the idle unload)."
            )
        if len(full_text) // 3 + budget > loaded_ctx:
            print(
                f"[lmstudio] warning: input plus output budget may exceed the {loaded_ctx}-token context; "
                "the answer could be cut off.",
                file=sys.stderr,
            )

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body: dict[str, object] = {"model": model, "messages": messages, "max_tokens": budget, "ttl": ttl}
    if effort != "default":
        body["reasoning_effort"] = effort
    temperature = os.environ.get("LMSTUDIO_TEMPERATURE")
    if temperature:
        body["temperature"] = float(temperature)
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    timeout = int(os.environ.get("LMSTUDIO_TIMEOUT", LMSTUDIO_TIMEOUT_SECONDS))
    _retries: list[int] = []
    t0 = time.monotonic()
    try:
        with _urlopen(req, timeout=timeout, _retries=_retries) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        if e.code == 404 or "not found" in detail.lower():
            hint = f" Model '{model}' is not available: list installed models with `lms ls`, download one with `lms get`."
        elif "reasoning" in detail.lower():
            hint = " This model may not accept reasoning_effort: set LMSTUDIO_REASONING_EFFORT=default to omit it."
        else:
            hint = ""
        raise RuntimeError(f"LM Studio HTTP {e.code} at {base}: {detail}{hint}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"LM Studio not reachable at {base} ({e.reason}). "
            "Start the server: lms server start (or open the LM Studio app)."
        ) from e
    except TimeoutError as e:
        raise RuntimeError(
            f"LM Studio did not answer within {timeout}s. Use a smaller input or model, or raise LMSTUDIO_TIMEOUT "
            "(and the Bash tool timeout)."
        ) from e
    elapsed = time.monotonic() - t0

    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError(f"LM Studio returned no choices (full response: {result})")
    choice = choices[0]
    message = choice.get("message") or {}
    content = (message.get("content") or "").strip()
    reasoning = (message.get("reasoning_content") or "").strip()
    finish = choice.get("finish_reason", "unknown")
    usage = result.get("usage") or {}
    tok_in = usage.get("prompt_tokens", "?")
    tok_out = usage.get("completion_tokens", "?")

    if isinstance(tok_in, int):
        ctx = loaded_ctx if loaded_ctx is not None else _lmstudio_loaded_context(base, model)
        if ctx is not None and tok_in >= ctx - 64:
            raise RuntimeError(
                f"LM Studio counted {tok_in} prompt tokens against a {ctx}-token context window: the input was "
                "truncated, so the review would cover a partial prompt. Raise this model's context length in "
                "LM Studio's model settings (loading it by hand with `lms load` disables the idle unload)."
            )
        expected = _estimate_tokens(full_text)
        if expected > 2000 and tok_in < expected * 0.6:
            print(
                f"[lmstudio] possible truncation: the server counted {tok_in} prompt tokens "
                f"but the input is about {expected}.",
                file=sys.stderr,
            )

    if not content:
        if reasoning:
            raise RuntimeError(
                f"LM Studio returned only reasoning, no answer (finish_reason={finish}). The token budget ran out "
                "while thinking: raise --max-tokens, or use a model or setting with thinking off."
            )
        raise RuntimeError(f"LM Studio returned no content (finish_reason={finish}; response: {result})")
    if finish == "length":
        print(
            "[lmstudio] finish_reason=length: the answer was cut off; raise --max-tokens for the full text.",
            file=sys.stderr,
        )

    tok_per_s: float | str = tok_out / elapsed if isinstance(tok_out, int) and elapsed > 0 else "?"
    _emit_stats("lmstudio", model, tok_in, tok_out, elapsed, tok_per_s, retries=_retries[0] if _retries else 0)
    return content


def call_codex(prompt: str, model: str | None, system: str | None, _max_tokens: int) -> str:
    """Invoke the Codex CLI companion script and return its stdout.

    Args:
        prompt: User message to send as the Codex task.
        model: Optional model identifier forwarded to the Codex CLI.
        system: Optional system instruction prepended to the task string.
        _max_tokens: Unused — Codex CLI controls depth via --effort, not token limit.

    Returns:
        The stripped stdout output from the Codex CLI companion.
    """
    # Locate the latest installed Codex CLI companion script
    cache = Path.home() / ".claude" / "plugins" / "cache" / "openai-codex" / "codex"
    if not cache.is_dir():
        raise RuntimeError(
            "Codex plugin not installed. Run: claude plugin install codex@openai-codex"
        )
    versions = sorted(
        (v.name for v in cache.iterdir() if v.is_dir()),
        key=_version_key,
    )
    if not versions:
        raise RuntimeError("No Codex plugin version found in cache.")
    companion = cache / versions[-1] / "scripts" / "codex-companion.mjs"
    if not companion.exists():
        raise RuntimeError(f"Codex companion not found at: {companion}")

    # Combine system prompt with user message — Codex `task` takes a single task string
    task = f"{system}\n\n{prompt}" if system else prompt

    cmd = ["node", str(companion), "task", task]
    if model:
        cmd += ["--model", model]

    try:
        t0 = time.monotonic()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elapsed = time.monotonic() - t0
    except FileNotFoundError:
        raise RuntimeError("'node' not found in PATH — install Node.js to use the Codex provider")
    except subprocess.TimeoutExpired as e:
        partial = (e.stdout or "").strip()
        hint = f"\nPartial output: {partial[:200]}" if partial else ""
        raise RuntimeError(f"Codex task timed out after 300s{hint}")
    if result.returncode != 0:
        raise RuntimeError(
            f"Codex task failed (exit {result.returncode}): {result.stderr[:500]}"
        )
    output = result.stdout.strip()
    if not output:
        raise RuntimeError("Codex returned empty output")
    _emit_stats("codex", model or "default", "?", "?", elapsed, "n/a")
    return output


def resolve_config_role(config_path: str, role_path: str) -> tuple[str, str | None]:
    """Resolve a dot-separated role path against models.json and return provider and model.

    Args:
        config_path: Filesystem path to the models.json config file.
        role_path: Dot-separated key path into the config (e.g. "vet.full.critic").

    Returns:
        A tuple of (provider, model) where model may be None if not specified in config.
    """
    with open(config_path) as f:
        config: dict[str, object] = json.load(f)
    parts = role_path.split(".")
    # Walk the config tree; narrowed to dict at each step before subscripting.
    node: dict[str, object] = config
    for part in parts:
        if part.startswith("_"):
            raise RuntimeError(
                f"Role '{role_path}' references metadata key '{part}' — check role path spelling"
            )
        raw = node.get(part)
        if raw is None:
            raise RuntimeError(
                f"Role '{role_path}' not found in config {config_path} (missing '{part}')"
            )
        if not isinstance(raw, dict):
            raise RuntimeError(
                f"Role '{role_path}': expected a dict at '{part}', got {type(raw).__name__}"
            )
        node = raw
    if "provider" not in node:
        raise RuntimeError(
            f"Role '{role_path}' has no 'provider' key in config {config_path}"
        )
    provider = str(node["provider"])
    raw_model = node.get("model")
    model: str | None = str(raw_model) if raw_model is not None else None
    if model is None and provider == "ollama":
        default = config.get("_default_local_model")
        model = str(default) if default is not None else None
    return provider, model


def main() -> None:
    """Parse arguments, read prompt from stdin, dispatch to the selected provider."""
    parser = argparse.ArgumentParser(description="Call an external LLM provider")
    parser.add_argument("--provider", help="Provider: gemini | xai | openai | groq | ollama | lmstudio | codex")
    parser.add_argument("--model", default=None, help="Model identifier (overrides config)")
    parser.add_argument("--system", default=None, help="System prompt")
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--config", default=None, help="Path to models.json config file")
    parser.add_argument(
        "--role", default=None, help="Dot-separated role in config (e.g. vet.full.critic)"
    )
    args = parser.parse_args()

    provider: str | None = args.provider
    model: str | None = args.model

    if args.role and not args.config:
        print("WARNING: --role requires --config; --role ignored", file=sys.stderr)

    if args.config and args.role:
        try:
            cfg_provider, cfg_model = resolve_config_role(args.config, args.role)
            if not provider:
                provider = cfg_provider
            if model is None:
                model = cfg_model
        except Exception as cfg_err:
            print(f"ERROR (config): {cfg_err}", file=sys.stderr)
            sys.exit(1)

    if not provider:
        print("ERROR: --provider is required (or use --config + --role)", file=sys.stderr)
        sys.exit(1)

    prompt = sys.stdin.read().strip()
    if not prompt:
        print("ERROR: empty prompt on stdin", file=sys.stderr)
        sys.exit(1)

    # Apply default models when none specified
    defaults: dict[str, str] = {
        "gemini": "gemini-2.5-pro",
        "xai": "grok-4.3",
        "openai": "gpt-5",
        "groq": "meta-llama/llama-4-scout-17b-16e-instruct",
        "ollama": "qwen3:32b",
    }
    if model is None and provider in defaults:
        model = defaults[provider]

    try:
        if provider == "gemini":
            response = call_gemini(prompt, model, args.system, args.max_tokens)
        elif provider == "xai":
            response = call_xai(prompt, model, args.system, args.max_tokens)
        elif provider == "openai":
            response = call_openai(prompt, model, args.system, args.max_tokens)
        elif provider == "groq":
            response = call_groq(prompt, model, args.system, args.max_tokens)
        elif provider == "ollama":
            response = call_ollama(prompt, model, args.system, args.max_tokens)
        elif provider == "lmstudio":
            response = call_lmstudio(prompt, model, args.system, args.max_tokens)
        elif provider == "codex":
            response = call_codex(prompt, model, args.system, args.max_tokens)
        elif provider == "claude":
            print(
                "ERROR: provider 'claude' is not callable via llm_call.py — "
                "dispatch Claude voices via the Agent tool in tao.md instead.",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            print(f"ERROR: unknown provider: {provider}", file=sys.stderr)
            sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code} from {provider}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR ({provider}): {e}", file=sys.stderr)
        sys.exit(1)

    print(response)


if __name__ == "__main__":
    main()
