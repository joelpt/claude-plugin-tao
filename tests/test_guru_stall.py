"""Tests for scripts/guru_stall.py roster/invocation/round-aware report-out classification.

Stdlib unittest only. Messages mirror the team-lead inbox shape: dicts with `from` and `text`.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

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


class InboxPath(unittest.TestCase):
    def test_explicit_path_used_verbatim(self):
        self.assertEqual(guru_stall.inbox_path("/x/inbox.json"), Path("/x/inbox.json"))


if __name__ == "__main__":
    unittest.main()
