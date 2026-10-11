"""Tests for scripts/llm_call.py: local-voice providers (LM Studio, Ollama) and config resolution.

Stdlib unittest only (the repo has no third-party dependencies). Network calls are replaced by a fake
``_urlopen`` that records requests and serves canned responses.
"""

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from collections.abc import Mapping
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("llm_call", ROOT / "scripts" / "llm_call.py")
assert _spec is not None and _spec.loader is not None
llm_call = importlib.util.module_from_spec(_spec)
sys.modules["llm_call"] = llm_call
_spec.loader.exec_module(llm_call)


class _FakeResp:
    def __init__(self, payload: object) -> None:
        self._bytes = payload if isinstance(payload, bytes) else json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._bytes

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False


class _FakeNet:
    """Routes by URL suffix; a value that is an Exception is raised instead of returned."""

    def __init__(self, routes: Mapping[str, object]) -> None:
        self.routes = routes
        self.requests: list[tuple[str, dict | None]] = []

    def __call__(self, req, timeout, _retries=None):  # noqa: ANN001
        url = req.full_url
        body = json.loads(req.data) if req.data else None
        self.requests.append((url, body))
        for suffix, value in self.routes.items():
            if url.endswith(suffix):
                if isinstance(value, BaseException):
                    raise value
                return _FakeResp(value)
        raise AssertionError(f"unrouted request: {url}")

    def posts(self) -> list[tuple[str, dict]]:
        return [(u, b) for u, b in self.requests if b is not None]


def _http_error(url: str, code: int, body: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, code, "err", {}, io.BytesIO(body.encode()))  # type: ignore[arg-type]


def _chat_ok(content: str = "A real review.", reasoning: str = "", finish: str = "stop", prompt_tokens: int = 500) -> dict:
    return {
        "choices": [{"message": {"content": content, "reasoning_content": reasoning}, "finish_reason": finish}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": 120},
    }


def _models(loaded_ctx: int | None, key: str = "m1") -> dict:
    instances = [] if loaded_ctx is None else [{"id": key, "config": {"context_length": loaded_ctx}}]
    return {"models": [{"key": key, "loaded_instances": instances}]}


@contextlib.contextmanager
def _env(**kv: str):
    with mock.patch.dict(os.environ, kv, clear=False):
        yield


def _run(fn, *args, **kwargs):  # noqa: ANN001
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        try:
            return fn(*args, **kwargs), err.getvalue(), None
        except Exception as exc:  # noqa: BLE001
            return None, err.getvalue(), exc


BASE = "http://127.0.0.1:44444/v1"


class LmStudioBaseUrl(unittest.TestCase):
    def test_env_var_wins(self) -> None:
        with _env(LMSTUDIO_BASE_URL="http://example:9/v1/"):
            self.assertEqual(llm_call._lmstudio_base_url(), "http://example:9/v1")

    def test_port_read_from_server_config(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "http-server-config.json"
            cfg.write_text(json.dumps({"port": 44444}))
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("LMSTUDIO_BASE_URL", None)
                self.assertEqual(llm_call._lmstudio_base_url(config_path=cfg), BASE)

    def test_falls_back_to_default_port(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LMSTUDIO_BASE_URL", None)
            self.assertEqual(
                llm_call._lmstudio_base_url(config_path=Path("/nonexistent/x.json")), "http://127.0.0.1:1234/v1"
            )


class CallLmStudio(unittest.TestCase):
    def _call(self, net: _FakeNet, *, model: str | None = "m1", prompt: str = "plan text", max_tokens: int = 1000, env: dict | None = None):
        with _env(LMSTUDIO_BASE_URL=BASE, **(env or {})), mock.patch.object(llm_call, "_urlopen", net):
            return _run(llm_call.call_lmstudio, prompt, model, "be a skeptic", max_tokens)

    def test_request_shape_and_default_ttl(self) -> None:
        net = _FakeNet({"/api/v1/models": _models(None), "/chat/completions": _chat_ok()})
        out, err, exc = self._call(net)
        self.assertIsNone(exc, exc)
        self.assertEqual(out, "A real review.")
        (url, body), = net.posts()
        self.assertEqual(url, f"{BASE}/chat/completions")
        self.assertEqual(body["model"], "m1")
        self.assertEqual(body["ttl"], 600)
        self.assertEqual([m["role"] for m in body["messages"]], ["system", "user"])
        self.assertIn("[tao-stats] provider=lmstudio model=m1", err)

    def test_thinking_is_off_by_default_and_gets_no_allowance(self) -> None:
        net = _FakeNet({"/api/v1/models": _models(None), "/chat/completions": _chat_ok()})
        self._call(net)
        body = net.posts()[0][1]
        self.assertEqual(body["reasoning_effort"], "none")
        self.assertEqual(body["max_tokens"], 1000)

    def test_reasoning_effort_override_adds_a_thinking_allowance(self) -> None:
        net = _FakeNet({"/api/v1/models": _models(None), "/chat/completions": _chat_ok()})
        self._call(net, env={"LMSTUDIO_REASONING_EFFORT": "medium"})
        body = net.posts()[0][1]
        self.assertEqual(body["reasoning_effort"], "medium")
        self.assertGreater(body["max_tokens"], 1000)

    def test_reasoning_effort_default_omits_the_parameter(self) -> None:
        net = _FakeNet({"/api/v1/models": _models(None), "/chat/completions": _chat_ok()})
        self._call(net, env={"LMSTUDIO_REASONING_EFFORT": "default"})
        body = net.posts()[0][1]
        self.assertNotIn("reasoning_effort", body)
        self.assertGreater(body["max_tokens"], 1000)

    def test_rejected_reasoning_parameter_names_the_override(self) -> None:
        url = f"{BASE}/chat/completions"
        err_body = '{"error":{"message":"Unrecognized key reasoning_effort"}}'
        net = _FakeNet({"/api/v1/models": _models(None), "/chat/completions": _http_error(url, 400, err_body)})
        _, _, exc = self._call(net)
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn("LMSTUDIO_REASONING_EFFORT=default", str(exc))

    def test_ttl_overridable_by_env(self) -> None:
        net = _FakeNet({"/api/v1/models": _models(None), "/chat/completions": _chat_ok()})
        self._call(net, env={"LMSTUDIO_TTL": "20"})
        self.assertEqual(net.posts()[0][1]["ttl"], 20)

    def test_no_model_configured_is_actionable(self) -> None:
        _, _, exc = self._call(_FakeNet({}), model=None)
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn("no model configured", str(exc))

    def test_reasoning_only_is_a_failure_not_a_review(self) -> None:
        net = _FakeNet({"/api/v1/models": _models(None), "/chat/completions": _chat_ok(content="", reasoning="thinking...", finish="length")})
        _, _, exc = self._call(net)
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn("reasoning", str(exc))
        self.assertIn("--max-tokens", str(exc))

    def test_length_cutoff_with_content_returns_content_and_warns(self) -> None:
        net = _FakeNet({"/api/v1/models": _models(None), "/chat/completions": _chat_ok(content="partial", finish="length")})
        out, err, exc = self._call(net)
        self.assertIsNone(exc, exc)
        self.assertEqual(out, "partial")
        self.assertIn("finish_reason=length", err)

    def test_model_not_found_names_the_fix(self) -> None:
        url = f"{BASE}/chat/completions"
        net = _FakeNet({"/api/v1/models": _models(None), "/chat/completions": _http_error(url, 404, '{"error":{"message":"model not found"}}')})
        _, _, exc = self._call(net)
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn("lms get", str(exc))
        self.assertNotIn("not reachable", str(exc))

    def test_unreachable_names_url_and_fix(self) -> None:
        net = _FakeNet({"/api/v1/models": urllib.error.URLError("refused"), "/chat/completions": urllib.error.URLError("refused")})
        _, _, exc = self._call(net)
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn(BASE, str(exc))
        self.assertIn("lms server start", str(exc))

    def test_input_that_cannot_fit_loaded_context_fails_before_posting(self) -> None:
        net = _FakeNet({"/api/v1/models": _models(4096), "/chat/completions": _chat_ok()})
        _, _, exc = self._call(net, prompt="word " * 20000)
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn("context", str(exc))
        self.assertEqual(net.posts(), [])

    def test_prompt_filling_the_context_after_the_call_is_truncation(self) -> None:
        routes = {"/api/v1/models": _models(8192), "/chat/completions": _chat_ok(prompt_tokens=8190)}
        _, _, exc = self._call(_FakeNet(routes), prompt="short")
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn("truncated", str(exc))

    def test_suspiciously_few_prompt_tokens_only_warns(self) -> None:
        routes = {"/api/v1/models": _models(65536), "/chat/completions": _chat_ok(prompt_tokens=100)}
        out, err, exc = self._call(_FakeNet(routes), prompt="x" * 40000)
        self.assertIsNone(exc, exc)
        self.assertEqual(out, "A real review.")
        self.assertIn("possible truncation", err)


class CallOllama(unittest.TestCase):
    URL = "http://localhost:11434/api/chat"

    def _call(self, net: _FakeNet, prompt: str = "plan text"):
        with mock.patch.object(llm_call, "_urlopen", net):
            return _run(llm_call.call_ollama, prompt, "qwen3:32b", "be a skeptic", 1000)

    def test_model_not_found_is_not_reported_as_unreachable(self) -> None:
        net = _FakeNet({"/api/chat": _http_error(self.URL, 404, '{"error":"model \'qwen3:32b\' not found"}')})
        _, _, exc = self._call(net)
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn("ollama pull qwen3:32b", str(exc))
        self.assertNotIn("not reachable", str(exc))

    def test_connection_refused_is_reported_as_unreachable(self) -> None:
        net = _FakeNet({"/api/chat": urllib.error.URLError("refused")})
        _, _, exc = self._call(net)
        self.assertIn("not reachable", str(exc))

    def test_request_sets_keep_alive_and_context(self) -> None:
        ok = {"message": {"content": "review"}, "prompt_eval_count": 300, "eval_count": 50, "eval_duration": 1_000_000_000}
        net = _FakeNet({"/api/chat": ok})
        out, _, exc = self._call(net, prompt="y" * 30000)
        self.assertIsNone(exc, exc)
        self.assertEqual(out, "review")
        body = net.posts()[0][1]
        self.assertEqual(body["keep_alive"], "10m")
        self.assertGreaterEqual(body["options"]["num_ctx"], 30000 // 4 + body["options"]["num_predict"])

    def test_thinking_only_reply_is_a_failure(self) -> None:
        net = _FakeNet({"/api/chat": {"message": {"content": "", "thinking": "hmm"}, "done_reason": "length", "prompt_eval_count": 10}})
        _, _, exc = self._call(net)
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn("reasoning", str(exc))

    def test_prompt_filling_num_ctx_is_truncation(self) -> None:
        net = _FakeNet({"/api/chat": {"message": {"content": "review"}, "prompt_eval_count": 10**6}})
        _, _, exc = self._call(net)
        self.assertIsInstance(exc, RuntimeError)
        self.assertIn("truncated", str(exc))


class ConfigResolution(unittest.TestCase):
    def _cfg(self, roles: dict) -> str:
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"_default_local_model": "qwen3:32b", "vet": {"standard": roles}}, fh)
        fh.close()
        self.addCleanup(os.unlink, fh.name)
        return fh.name

    def test_ollama_without_model_gets_the_default(self) -> None:
        path = self._cfg({"local": {"provider": "ollama", "model": None}})
        self.assertEqual(llm_call.resolve_config_role(path, "vet.standard.local"), ("ollama", "qwen3:32b"))

    def test_lmstudio_never_inherits_the_ollama_default(self) -> None:
        path = self._cfg({"local": {"provider": "lmstudio", "model": None}})
        self.assertEqual(llm_call.resolve_config_role(path, "vet.standard.local"), ("lmstudio", None))

    def test_shipped_config_roles_name_known_providers_and_models(self) -> None:
        cfg = json.loads((ROOT / "config" / "models.json").read_text())
        known = {"claude", "xai", "openai", "groq", "codex", "ollama", "gemini", "lmstudio"}
        for depth in ("standard", "full"):
            for role, entry in cfg["vet"][depth].items():
                self.assertIn(entry["provider"], known, f"vet.{depth}.{role}")
                if entry["provider"] == "lmstudio":
                    self.assertTrue(entry["model"], f"vet.{depth}.{role} needs an explicit model key")


class MainDispatch(unittest.TestCase):
    def test_provider_lmstudio_is_dispatched(self) -> None:
        with mock.patch.object(llm_call, "call_lmstudio", return_value="voice") as call, mock.patch.object(
            sys, "argv", ["llm_call.py", "--provider=lmstudio", "--model=m1"]
        ), mock.patch.object(sys, "stdin", io.StringIO("hello")):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                llm_call.main()
        self.assertEqual(out.getvalue().strip(), "voice")
        self.assertEqual(call.call_args.args[1], "m1")


class ReferenceDocs(unittest.TestCase):
    """The vet references are executed by a model; their shell and labels must survive a plan full of backticks."""

    def _refs(self) -> list[Path]:
        return [ROOT / "references" / "vet-standard.md", ROOT / "references" / "vet-full.md"]

    def test_input_is_never_interpolated_inside_double_quotes(self) -> None:
        for ref in self._refs():
            self.assertFalse("printf '%s\\n' \"<input>\"" in ref.read_text(), f"{ref.name} pipes <input> through double quotes")

    def test_local_voice_is_labelled_provider_neutrally(self) -> None:
        for ref in self._refs():
            text = ref.read_text()
            self.assertFalse("## Ollama" in text, f"{ref.name} has an Ollama-only section heading")
            self.assertFalse("check ollama serve" in text, f"{ref.name} has an Ollama-only fix hint")

    def test_local_voice_call_has_a_long_bash_timeout(self) -> None:
        for ref in self._refs():
            self.assertTrue("600000" in ref.read_text(), f"{ref.name} does not set a 600000 ms Bash timeout for the local voice")


if __name__ == "__main__":
    unittest.main()
