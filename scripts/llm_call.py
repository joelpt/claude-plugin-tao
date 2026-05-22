#!/usr/bin/env python3
"""
Multi-provider LLM caller for tao consensus/challenge modes.
Reads prompt from stdin, writes response to stdout.

Usage (explicit provider):
  echo "prompt" | python3 llm_call.py --provider=<gemini|xai|ollama|codex> [--model=<name>]
      [--system=<text>] [--max-tokens=<int>]

Usage (config-based role):
  echo "prompt" | python3 llm_call.py --config=<path/to/models.json> --role=<section.role>
      [--system=<text>] [--max-tokens=<int>]
  # --provider and --model override config values when provided alongside --role

API keys (from ~/.zshenv — never hardcoded):
  GEMINI_API_KEY  — Google Gemini (generativelanguage API v1beta)
  XAI_API_KEY     — xAI Grok (OpenAI-compatible endpoint at api.x.ai)
  (Codex uses the OpenAI Codex CLI companion — no key var needed here)
  (Ollama needs no key — local endpoint at localhost:11434)
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
import urllib.request
import urllib.error


def _version_key(v: str) -> tuple[int, ...]:
    """Return a numeric tuple for semver-safe sorting of version directory names."""
    return tuple(int(x) for x in re.split(r"[.\-]", v.lstrip("v")) if x.isdigit())


def _urlopen(
    req: urllib.request.Request,
    timeout: int,
    _retries: list[int] | None = None,
) -> http.client.HTTPResponse:
    """Open a URL request, retrying up to 8 times on 529 with exponential backoff.

    Args:
        req: The request to open.
        timeout: Socket timeout in seconds.
        _retries: If provided, the number of retries performed is appended on success.
    """
    for attempt in range(9):
        try:
            response = urllib.request.urlopen(req, timeout=timeout)  # type: ignore[return-value]
            if _retries is not None:
                _retries.append(attempt)
            return response
        except urllib.error.HTTPError as e:
            if e.code == 529 and attempt < 8:
                delay = min(2**attempt + random.uniform(0, 1), 60)
                print(
                    f"[529 overloaded] retrying in {delay:.1f}s (attempt {attempt + 1}/8)…",
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
        provider: Provider name (gemini, xai, ollama, codex).
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
    """Call Google Gemini generateContent API and return the response text."""
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
    """Call the xAI OpenAI-compatible API and return the response message content."""
    model = model or "grok-4.3"
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise RuntimeError("XAI_API_KEY not set in environment")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
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
    content = choices[0]["message"]["content"]
    usage = result.get("usage") or {}
    tok_in = usage.get("prompt_tokens", "?")
    tok_out = usage.get("completion_tokens", "?")
    tok_per_s: float | str = tok_out / elapsed if isinstance(tok_out, int) and elapsed > 0 else "?"
    _emit_stats("xai", model, tok_in, tok_out, elapsed, tok_per_s, retries=_retries[0] if _retries else 0)
    return content


def call_ollama(prompt: str, model: str | None, system: str | None, max_tokens: int) -> str:
    """Call the local Ollama /api/chat endpoint and return the assistant message content."""
    model = model or "qwen3:32b"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    _THINKING_MODELS = {"qwen3", "deepseek-r1"}
    thinking = any(model.startswith(prefix) for prefix in _THINKING_MODELS)

    # Thinking tokens consume from the same num_predict budget as content tokens.
    # Add a fixed 8192-token thinking overhead so CoT doesn't crowd out the response.
    num_predict = max_tokens + 8192 if thinking else max_tokens

    body: dict[str, object] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": thinking,
        "options": {"num_predict": num_predict},
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
    with _urlopen(req, timeout=300, _retries=_retries) as resp:
        result = json.loads(resp.read())
    elapsed = time.monotonic() - t0

    error_msg = result.get("error")
    if error_msg:
        raise RuntimeError(f"Ollama error: {error_msg}")
    msg = result.get("message", {})
    content = msg.get("content") or msg.get("thinking")
    if not content:
        raise RuntimeError(f"Ollama returned no message content (response: {result})")

    tok_in = result.get("prompt_eval_count", "?")
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


def call_codex(prompt: str, model: str | None, system: str | None, _max_tokens: int) -> str:
    """Invoke the Codex CLI companion script and return its stdout."""
    # Codex CLI controls depth via --effort, not a token limit
    # Locate the latest installed Codex CLI companion script
    cache = os.path.expanduser("~/.claude/plugins/cache/openai-codex/codex")
    if not os.path.isdir(cache):
        raise RuntimeError(
            "Codex plugin not installed. Run: claude plugin install codex@openai-codex"
        )
    versions = sorted(
        (v for v in os.listdir(cache) if os.path.isdir(os.path.join(cache, v))),
        key=_version_key,
    )
    if not versions:
        raise RuntimeError("No Codex plugin version found in cache.")
    companion = os.path.join(cache, versions[-1], "scripts", "codex-companion.mjs")
    if not os.path.exists(companion):
        raise RuntimeError(f"Codex companion not found at: {companion}")

    # Combine system prompt with user message — Codex `task` takes a single task string
    task = f"{system}\n\n{prompt}" if system else prompt

    cmd = ["node", companion, "task", task]
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
    """Resolve a dot-separated role path (e.g. 'consensus.critic') against models.json."""
    with open(config_path) as f:
        config = json.load(f)
    parts = role_path.split(".")
    node = config
    for part in parts:
        if part.startswith("_"):
            raise RuntimeError(
                f"Role '{role_path}' references metadata key '{part}' — check role path spelling"
            )
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            raise RuntimeError(
                f"Role '{role_path}' not found in config {config_path} (missing '{part}')"
            )
    if not isinstance(node, dict) or "provider" not in node:
        raise RuntimeError(
            f"Role '{role_path}' has no 'provider' key in config {config_path}"
        )
    provider: str = node["provider"]
    model: str | None = node.get("model")
    if model is None and provider == "ollama":
        model = config.get("_default_local_model")
    return provider, model


def main() -> None:
    """Parse arguments, read prompt from stdin, dispatch to the selected provider."""
    parser = argparse.ArgumentParser(description="Call an external LLM provider")
    parser.add_argument("--provider", help="Provider: gemini | xai | ollama | codex")
    parser.add_argument("--model", default=None, help="Model identifier (overrides config)")
    parser.add_argument("--system", default=None, help="System prompt")
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--config", default=None, help="Path to models.json config file")
    parser.add_argument(
        "--role", default=None, help="Dot-separated role in config (e.g. consensus.critic)"
    )
    args = parser.parse_args()

    provider = args.provider
    model = args.model

    if args.role and not args.config:
        print("WARNING: --role requires --config; --role ignored", file=sys.stderr)

    if args.config and args.role:
        try:
            cfg_provider, cfg_model = resolve_config_role(args.config, args.role)
        except Exception as cfg_err:
            print(f"ERROR (config): {cfg_err}", file=sys.stderr)
            sys.exit(1)
        if not provider:
            provider = cfg_provider
        if model is None:
            model = cfg_model

    if not provider:
        print("ERROR: --provider is required (or use --config + --role)", file=sys.stderr)
        sys.exit(1)

    prompt = sys.stdin.read().strip()
    if not prompt:
        print("ERROR: empty prompt on stdin", file=sys.stderr)
        sys.exit(1)

    # Apply default models when none specified
    defaults = {"gemini": "gemini-2.5-pro", "xai": "grok-4.3", "ollama": "qwen3:32b"}
    if model is None and provider in defaults:
        model = defaults[provider]

    try:
        if provider == "gemini":
            response = call_gemini(prompt, model, args.system, args.max_tokens)
        elif provider == "xai":
            response = call_xai(prompt, model, args.system, args.max_tokens)
        elif provider == "ollama":
            response = call_ollama(prompt, model, args.system, args.max_tokens)
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
