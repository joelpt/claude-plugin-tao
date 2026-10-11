"""Tests for scripts/llm_call.py config resolution and provider dispatch, and for the vet references.

Stdlib unittest only (the repo has no third-party dependencies). tao routes its external voices to cloud
providers and subscriptions only; there is deliberately no local-model provider.
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("llm_call", ROOT / "scripts" / "llm_call.py")
assert _spec is not None and _spec.loader is not None
llm_call = importlib.util.module_from_spec(_spec)
sys.modules["llm_call"] = llm_call
_spec.loader.exec_module(llm_call)

CLOUD_PROVIDERS = {"claude", "xai", "openai", "groq", "codex", "gemini"}
LOCAL_WORDS = re.compile(r"ollama|lm ?studio|lmstudio|qwen|_default_local_model|local (model|voice)", re.IGNORECASE)


class ConfigResolution(unittest.TestCase):
    def _cfg(self, roles: dict) -> str:
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"vet": {"standard": roles}}, fh)
        fh.close()
        self.addCleanup(os.unlink, fh.name)
        return fh.name

    def test_role_resolves_to_its_configured_provider_and_model(self) -> None:
        path = self._cfg({"challenger": {"provider": "xai", "model": "grok-4.3"}})
        self.assertEqual(llm_call.resolve_config_role(path, "vet.standard.challenger"), ("xai", "grok-4.3"))

    def test_role_without_a_model_resolves_to_none(self) -> None:
        path = self._cfg({"analyst": {"provider": "codex", "model": None}})
        self.assertEqual(llm_call.resolve_config_role(path, "vet.standard.analyst"), ("codex", None))

    def test_metadata_keys_are_rejected(self) -> None:
        path = self._cfg({"challenger": {"provider": "xai", "model": "grok-4.3"}})
        with self.assertRaises(RuntimeError):
            llm_call.resolve_config_role(path, "vet._comment")

    def test_shipped_config_names_only_cloud_providers(self) -> None:
        cfg = json.loads((ROOT / "config" / "models.json").read_text())
        self.assertNotIn("_default_local_model", cfg)
        for depth in ("quick", "standard", "full"):
            for role, entry in cfg["vet"][depth].items():
                self.assertIn(entry["provider"], CLOUD_PROVIDERS, f"vet.{depth}.{role}")
        for provider in cfg["_providers"]:
            self.assertIn(provider, CLOUD_PROVIDERS)

    def test_shipped_config_has_no_local_role(self) -> None:
        cfg = json.loads((ROOT / "config" / "models.json").read_text())
        for depth in ("quick", "standard", "full"):
            self.assertNotIn("local", cfg["vet"][depth], f"vet.{depth} still has a local role")


class MainDispatch(unittest.TestCase):
    def _run_main(self, *argv: str) -> tuple[int | None, str]:
        err = io.StringIO()
        code: int | None = None
        with mock.patch.object(sys, "argv", ["llm_call.py", *argv]), mock.patch.object(
            sys, "stdin", io.StringIO("hello")
        ), contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                llm_call.main()
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
        return code, err.getvalue()

    def test_local_providers_are_unknown(self) -> None:
        for provider in ("ollama", "lmstudio"):
            code, err = self._run_main(f"--provider={provider}", "--model=m")
            self.assertEqual(code, 1, provider)
            self.assertTrue("unknown provider" in err, f"{provider}: {err[:120]}")

    def test_no_local_provider_functions_remain(self) -> None:
        for name in ("call_ollama", "call_lmstudio", "_lmstudio_base_url", "_ollama_num_ctx"):
            self.assertFalse(hasattr(llm_call, name), name)

    def test_cloud_provider_is_dispatched(self) -> None:
        with mock.patch.object(llm_call, "call_xai", return_value="voice") as call, mock.patch.object(
            sys, "argv", ["llm_call.py", "--provider=xai", "--model=grok-4.3"]
        ), mock.patch.object(sys, "stdin", io.StringIO("hello")):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                llm_call.main()
        self.assertEqual(out.getvalue().strip(), "voice")
        self.assertEqual(call.call_args.args[1], "grok-4.3")


class ReferenceDocs(unittest.TestCase):
    """The vet references are executed by a model; their shell must survive a plan full of backticks."""

    def _refs(self) -> list[Path]:
        return [ROOT / "references" / "vet-standard.md", ROOT / "references" / "vet-full.md"]

    def test_input_is_never_interpolated_inside_double_quotes(self) -> None:
        for ref in self._refs():
            self.assertFalse("printf '%s\\n' \"<input>\"" in ref.read_text(), f"{ref.name} pipes <input> through double quotes")

    def test_bash_voices_take_input_through_a_quoted_heredoc(self) -> None:
        for ref in self._refs():
            self.assertTrue("<<'TAO_RANDOM_EOF'" in ref.read_text(), f"{ref.name} has no quoted heredoc")

    def test_no_local_voice_is_referenced(self) -> None:
        paths = [*self._refs(), ROOT / "commands" / "vet.md", ROOT / "agents" / "consensus-synthesizer.md", ROOT / "README.md"]
        for path in paths:
            match = LOCAL_WORDS.search(path.read_text())
            self.assertIsNone(match, f"{path.name} still mentions a local model: {match.group(0) if match else ''}")
        self.assertFalse(
            "vet.standard.local" in "".join(p.read_text() for p in self._refs()), "a vet reference still calls the local role"
        )

    def test_depth_table_counts_voices_without_a_local_one(self) -> None:
        vet = (ROOT / "commands" / "vet.md").read_text()
        self.assertTrue("`--voices=1|2|3`" in vet, "vet.md still documents --voices=1|3|4")
        self.assertTrue("standard | 2 —" in vet and "full | 3 —" in vet, "vet.md depth table has stale voice counts")


if __name__ == "__main__":
    unittest.main()
