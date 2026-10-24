"""Tests for scripts/guru_stall.py roster/invocation/round-aware report-out classification.

Stdlib unittest only. Messages mirror the team-lead inbox shape: dicts with `from` and `text`.
"""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("guru_stall", ROOT / "scripts" / "guru_stall.py")
assert _spec is not None and _spec.loader is not None
guru_stall = importlib.util.module_from_spec(_spec)
sys.modules["guru_stall"] = guru_stall
_spec.loader.exec_module(guru_stall)

INV = "gc-a1b2"
ROSTER = [f"{INV}-linus", f"{INV}-guido", f"{INV}-carmack"]


def final(sender: str, inv: str = INV, rnd: int = 3, engaged: str = "guido, carmack", changed: str = "conceded X") -> dict:
    return {
        "from": sender,
        "text": f"[RT:{inv}|FINAL|r{rnd}] FINAL POSITION\nPEERS ENGAGED: {engaged}\nCHANGED: {changed}\nstance",
    }


def idle(sender: str) -> dict:
    return {"from": sender, "text": '{"type": "idle_notification"}'}


class Classify(unittest.TestCase):
    def test_all_roster_finals_accepted(self):
        msgs = [final(n) for n in ROSTER]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(sorted(r.accepted), sorted(ROSTER))
        self.assertEqual(r.premature, [])

    def test_missing_participant_not_accepted(self):
        msgs = [final(ROSTER[0]), final(ROSTER[1]), idle(ROSTER[2])]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(sorted(r.accepted), sorted(ROSTER[:2]))
        self.assertEqual(r.idle_unreported, [ROSTER[2]])

    def test_premature_final_flagged_not_counted(self):
        msgs = [final(ROSTER[0], rnd=1)]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.accepted, [])
        self.assertEqual(r.premature, [ROSTER[0]])

    def test_final_without_peer_engagement_is_premature(self):
        msgs = [final(ROSTER[0], engaged="")]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.accepted, [])
        self.assertEqual(r.premature, [ROSTER[0]])

    def test_engagement_must_name_a_roster_peer_other_than_self(self):
        msgs = [final(ROSTER[0], engaged="linus")]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.premature, [ROSTER[0]])

    def test_final_without_changed_line_is_premature(self):
        m = final(ROSTER[0])
        m["text"] = m["text"].replace("CHANGED:", "NOTE:")
        r = guru_stall.classify([m], INV, ROSTER, min_round=3)
        self.assertEqual(r.premature, [ROSTER[0]])

    def test_other_invocation_ignored(self):
        other = [f"gc-zzzz-{n.split('-')[-1]}" for n in ROSTER]
        msgs = [final(n, inv="gc-zzzz") for n in other]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.accepted, [])
        self.assertEqual(r.premature, [])

    def test_unrelated_teammate_ignored(self):
        msgs = [final("stranger"), {"from": "stranger", "text": "FINAL POSITION unrelated"}]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.accepted, [])

    def test_untagged_final_position_not_counted(self):
        msgs = [{"from": ROSTER[0], "text": "FINAL POSITION without header"}]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.accepted, [])

    def test_premature_then_valid_final_accepted(self):
        msgs = [final(ROSTER[0], rnd=1), final(ROSTER[0], rnd=3)]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.accepted, [ROSTER[0]])
        self.assertEqual(r.premature, [])

    def test_idle_after_final_not_listed_unreported(self):
        msgs = [final(ROSTER[0]), idle(ROSTER[0])]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.idle_unreported, [])

    def test_idle_from_non_roster_ignored(self):
        r = guru_stall.classify([idle("stranger")], INV, ROSTER, min_round=3)
        self.assertEqual(r.idle_unreported, [])

    def test_consecutive_roundtables_isolated(self):
        first = [final(n) for n in ROSTER]
        second_inv = "gc-c3d4"
        second_roster = [f"{second_inv}-{n.split('-')[-1]}" for n in ROSTER]
        r = guru_stall.classify(first, second_inv, second_roster, min_round=3)
        self.assertEqual(r.accepted, [])


class IdleAndStuck(unittest.TestCase):
    def test_earlier_idle_superseded_by_later_message(self):
        msgs = [idle(ROSTER[0]), {"from": ROSTER[0], "text": f"[RT:{INV}|REBUT|r2] working"}]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.idle_unreported, [])

    def test_idle_after_latest_message_is_unreported(self):
        msgs = [{"from": ROSTER[0], "text": f"[RT:{INV}|REBUT|r2] x"}, idle(ROSTER[0])]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.idle_unreported, [ROSTER[0]])

    def test_premature_sender_stays_stuck_after_idle(self):
        msgs = [final(ROSTER[0], rnd=1), idle(ROSTER[0])]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.premature, [ROSTER[0]])
        self.assertEqual(r.idle_unreported, [ROSTER[0]])

    def test_final_mentioning_idle_notification_still_accepted(self):
        m = final(ROSTER[0])
        m["text"] += "\nI saw an idle_notification earlier"
        r = guru_stall.classify([m], INV, ROSTER, min_round=3)
        self.assertEqual(r.accepted, [ROSTER[0]])

    def test_json_idle_type_detected(self):
        msgs = [{"from": ROSTER[0], "text": json.dumps({"type": "idle_notification"})}]
        r = guru_stall.classify(msgs, INV, ROSTER, min_round=3)
        self.assertEqual(r.idle_unreported, [ROSTER[0]])

    def test_non_dict_entries_skipped(self):
        r = guru_stall.classify([None, 3, "x", final(ROSTER[0])], INV, ROSTER, min_round=3)
        self.assertEqual(r.accepted, [ROSTER[0]])


class EngagedParsing(unittest.TestCase):
    def _check(self, engaged_line: str) -> list[str]:
        m = final(ROSTER[0])
        m["text"] = m["text"].replace("PEERS ENGAGED: guido, carmack", engaged_line)
        return guru_stall.classify([m], INV, ROSTER, min_round=3).accepted

    def test_markdown_bold_label(self):
        self.assertEqual(self._check("**PEERS ENGAGED:** guido, carmack"), [ROSTER[0]])

    def test_bullet_label(self):
        self.assertEqual(self._check("- PEERS ENGAGED: guido"), [ROSTER[0]])

    def test_at_prefix_and_punctuation(self):
        self.assertEqual(self._check("PEERS ENGAGED: @guido, (carmack)."), [ROSTER[0]])

    def test_full_prefixed_name(self):
        self.assertEqual(self._check(f"PEERS ENGAGED: {ROSTER[1]}"), [ROSTER[0]])


def run_poll(inbox: Path, polls: int, between=None) -> list[str]:
    """Run poll() for a fixed number of sleeps, returning printed lines."""
    count = {"n": 0}

    def fake_sleep(_seconds: float) -> None:
        count["n"] += 1
        if between:
            between(count["n"])

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        guru_stall.poll(inbox, INV, ROSTER, 3, sleep=fake_sleep, max_polls=polls)
    return buf.getvalue().splitlines()


class Poll(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.inbox = Path(self.tmp.name) / "team-lead.json"

    def test_missing_file_warns_once(self):
        lines = run_poll(self.inbox, 3)
        self.assertEqual(len([x for x in lines if x.startswith("INBOX_MISSING")]), 1)

    def test_mid_write_json_skipped_silently(self):
        self.inbox.write_text("[{")
        lines = run_poll(self.inbox, 2)
        self.assertEqual([x for x in lines if x.startswith(("PROGRESS", "STALL"))], [])

    def test_non_list_json_does_not_crash(self):
        self.inbox.write_text('{"a": 1}')
        lines = run_poll(self.inbox, 2)
        self.assertTrue(any(x.startswith("INBOX_INVALID") for x in lines))

    def test_null_element_does_not_crash(self):
        self.inbox.write_text(json.dumps([None, final(ROSTER[0])]))
        lines = run_poll(self.inbox, 1)
        self.assertIn(f"PROGRESS reported=1/3 [{ROSTER[0]}]", lines)

    def test_stall_fires_after_quiet_window_and_repeats(self):
        self.inbox.write_text(json.dumps([final(ROSTER[0], rnd=1), idle(ROSTER[0])]))
        lines = run_poll(self.inbox, 13)
        stalls = [x for x in lines if x.startswith("STALL")]
        self.assertEqual(len(stalls), 2)
        self.assertIn(ROSTER[0], stalls[0])

    def test_stall_not_before_window(self):
        self.inbox.write_text(json.dumps([idle(ROSTER[0])]))
        lines = run_poll(self.inbox, 5)
        self.assertEqual([x for x in lines if x.startswith("STALL")], [])

    def test_progress_resets_quiet_timer(self):
        self.inbox.write_text(json.dumps([idle(ROSTER[0])]))

        def between(n: int) -> None:
            if n == 5:
                self.inbox.write_text(json.dumps([idle(ROSTER[0]), final(ROSTER[1])]))

        lines = run_poll(self.inbox, 10, between)
        self.assertEqual([x for x in lines if x.startswith("STALL")], [])

    def test_all_reported_exits(self):
        self.inbox.write_text(json.dumps([final(n) for n in ROSTER]))
        lines = run_poll(self.inbox, 50)
        self.assertTrue(lines[-1].startswith("ALL_REPORTED"))


class InboxPath(unittest.TestCase):
    def test_explicit_path_used_verbatim(self):
        self.assertEqual(guru_stall.inbox_path("/x/inbox.json"), Path("/x/inbox.json"))

    def test_team_name_branch(self):
        with mock.patch.object(Path, "home", return_value=Path("/h")):
            self.assertEqual(
                guru_stall.inbox_path("session-ab12cd34"),
                Path("/h/.claude/teams/session-ab12cd34/inboxes/team-lead.json"),
            )


if __name__ == "__main__":
    unittest.main()
