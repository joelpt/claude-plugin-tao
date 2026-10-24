"""Tests for scripts/guru_stats.py per-teammate roundtable statistics.

Stdlib unittest only. Fixtures mirror the Claude Code subagent transcript shape: one JSON object
per line, `assistant` rows carrying `message.usage`, and `user` rows carrying teammate mail.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import guru_stats  # noqa: E402

INV = "gc-a1b2"
SESSION = "sess-1234"
Row = dict[str, object]


def usage(inp: int = 1, create: int = 100, read: int = 0, out: int = 10) -> dict[str, int]:
    """Build a usage record with the four token categories."""
    return {
        "input_tokens": inp,
        "cache_creation_input_tokens": create,
        "cache_read_input_tokens": read,
        "output_tokens": out,
    }


def assistant(msg_id: str, ts: str, use: dict[str, int], tool_uses: list[Row] | None = None) -> Row:
    """Build an assistant transcript row."""
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {"id": msg_id, "usage": use, "content": tool_uses or [{"type": "text", "text": "hi"}]},
    }


def send(block_id: str, to: str, message: object) -> Row:
    """Build a SendMessage tool_use block."""
    return {"type": "tool_use", "id": block_id, "name": "SendMessage", "input": {"to": to, "message": message}}


def mail(ts: str, sender: str, body: str) -> Row:
    """Build a user row carrying one teammate message."""
    text = f'<teammate-message teammate_id="{sender}" summary="s">\n{body}\n</teammate-message>'
    return {"type": "user", "timestamp": ts, "message": {"content": text}}


def final_text(engaged: str) -> str:
    """Build a conforming FINAL POSITION message body."""
    return f"[RT:{INV}|FINAL|r3] FINAL POSITION\nPEERS ENGAGED: {engaged}\nCHANGED: conceded a point\nstance"


class Fixture:
    """Builds a projects dir holding one session's subagent transcripts."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.projects = Path(self._tmp.name)
        self.subagents = self.projects / "-some-project" / SESSION / "subagents"
        self.subagents.mkdir(parents=True)

    def add(self, name: str, rows: list[Row], agent_id: str | None = None) -> None:
        """Write a teammate transcript and its meta file."""
        stem = f"agent-a{name}-{agent_id or 'abc123'}"
        (self.subagents / f"{stem}.meta.json").write_text(json.dumps({"name": name}))
        (self.subagents / f"{stem}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    def close(self) -> None:
        """Remove the temporary projects dir."""
        self._tmp.cleanup()


class AnalyzeTranscriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.roster = [f"{INV}-linus", f"{INV}-guido"]

    def analyze(self, rows: list[Row], name: str | None = None) -> guru_stats.Stats:
        """Write one transcript and analyze it against the fixture roster."""
        name = name or self.roster[0]
        self.fx.add(name, rows)
        found = guru_stats.find_transcripts(self.fx.projects, SESSION, [name])
        return guru_stats.analyze(name, found[name], self.roster)

    def test_tokens_sum_all_categories_and_split_out_output(self) -> None:
        rows = [
            assistant("m1", "2026-10-24T09:00:00.000Z", usage(inp=2, create=100, read=0, out=10)),
            assistant("m2", "2026-10-24T09:00:05.000Z", usage(inp=3, create=0, read=100, out=20)),
        ]
        stats = self.analyze(rows)
        self.assertEqual(stats.tokens_total, 2 + 100 + 10 + 3 + 100 + 20)
        self.assertEqual(stats.tokens_output, 30)

    def test_usage_deduplicated_by_message_id(self) -> None:
        # Streaming writes one API message across several rows that repeat the same usage.
        rows = [
            assistant("m1", "2026-10-24T09:00:00.000Z", usage(out=10)),
            assistant("m1", "2026-10-24T09:00:01.000Z", usage(out=10)),
            assistant("m1", "2026-10-24T09:00:02.000Z", usage(out=10)),
        ]
        self.assertEqual(self.analyze(rows).tokens_output, 10)

    def test_duplicate_message_id_keeps_the_largest_usage(self) -> None:
        rows = [
            assistant("m1", "2026-10-24T09:00:00.000Z", usage(out=4)),
            assistant("m1", "2026-10-24T09:00:01.000Z", usage(out=10)),
        ]
        self.assertEqual(self.analyze(rows).tokens_output, 10)

    def test_messages_sent_counts_text_sends_but_not_protocol_frames(self) -> None:
        blocks = [
            send("t1", f"{INV}-guido", "[RT:gc-a1b2|OPEN|r1] hello"),
            send("t2", "team-lead", final_text("guido")),
            send("t3", "team-lead", {"type": "shutdown_response", "approve": True}),
        ]
        rows = [assistant("m1", "2026-10-24T09:00:00.000Z", usage(), blocks)]
        self.assertEqual(self.analyze(rows).sent, 2)

    def test_repeated_tool_use_id_counted_once(self) -> None:
        blocks = [send("t1", f"{INV}-guido", "hello")]
        rows = [
            assistant("m1", "2026-10-24T09:00:00.000Z", usage(), blocks),
            assistant("m1", "2026-10-24T09:00:01.000Z", usage(), blocks),
        ]
        self.assertEqual(self.analyze(rows).sent, 1)

    def test_received_excludes_spawn_prompt_and_protocol_frames(self) -> None:
        rows = [
            mail("2026-10-24T09:00:00.000Z", "team-lead", "you are linus ..."),
            mail("2026-10-24T09:00:10.000Z", f"{INV}-guido", "[RT:gc-a1b2|OPEN|r1] my view"),
            mail("2026-10-24T09:00:20.000Z", "team-lead", "Round 2. Respond."),
            mail("2026-10-24T09:00:30.000Z", "team-lead", '{"type":"shutdown_request","reason":"done"}'),
        ]
        self.assertEqual(self.analyze(rows).received, 2)

    def test_protocol_frame_followed_by_prose_is_not_counted(self) -> None:
        frame = '{"type":"shutdown_request","reason":"done"}\n\nThis is a shutdown request. To approve it, call SendMessage.'
        rows = [
            mail("2026-10-24T09:00:00.000Z", "team-lead", "spawn"),
            mail("2026-10-24T09:00:10.000Z", f"{INV}-guido", "[RT:gc-a1b2|OPEN|r1] my view"),
            mail("2026-10-24T09:00:20.000Z", "team-lead", frame),
        ]
        self.assertEqual(self.analyze(rows).received, 1)

    def test_two_mail_blocks_in_one_row_both_count(self) -> None:
        body = "\n".join(
            [
                '<teammate-message teammate_id="a">\nfirst\n</teammate-message>',
                '<teammate-message teammate_id="b">\nsecond\n</teammate-message>',
            ]
        )
        rows = [
            mail("2026-10-24T09:00:00.000Z", "team-lead", "spawn"),
            {"type": "user", "timestamp": "2026-10-24T09:00:05.000Z", "message": {"content": body}},
        ]
        self.assertEqual(self.analyze(rows).received, 2)

    def test_mail_in_list_content_is_counted(self) -> None:
        text = '<teammate-message teammate_id="a">\nhello\n</teammate-message>'
        rows = [
            mail("2026-10-24T09:00:00.000Z", "team-lead", "spawn"),
            {"type": "user", "timestamp": "2026-10-24T09:00:05.000Z", "message": {"content": [{"type": "text", "text": text}]}},
        ]
        self.assertEqual(self.analyze(rows).received, 1)

    def test_wall_clock_spans_first_to_last_timestamp(self) -> None:
        rows = [
            assistant("m1", "2026-10-24T09:00:00.000Z", usage()),
            {"type": "attachment"},
            assistant("m2", "2026-10-24T09:01:23.500Z", usage()),
        ]
        self.assertAlmostEqual(self.analyze(rows).seconds, 83.5)

    def test_final_engagement_names_resolve_to_roster_members(self) -> None:
        blocks = [send("t1", "team-lead", final_text("guido, @Carmack."))]
        rows = [assistant("m1", "2026-10-24T09:00:00.000Z", usage(), blocks)]
        roster = [f"{INV}-linus", f"{INV}-guido", f"{INV}-carmack"]
        self.fx.add(roster[0], rows)
        found = guru_stats.find_transcripts(self.fx.projects, SESSION, [roster[0]])
        stats = guru_stats.analyze(roster[0], found[roster[0]], roster)
        self.assertEqual(stats.engaged, {f"{INV}-guido", f"{INV}-carmack"})

    def test_engagement_ignores_self_and_unknown_names(self) -> None:
        blocks = [send("t1", "team-lead", final_text("linus, nobody"))]
        rows = [assistant("m1", "2026-10-24T09:00:00.000Z", usage(), blocks)]
        self.assertEqual(self.analyze(rows).engaged, set())


class FindTranscriptsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = Fixture()
        self.addCleanup(self.fx.close)

    def test_finds_roster_members_only(self) -> None:
        self.fx.add(f"{INV}-linus", [])
        self.fx.add("unrelated-agent", [])
        found = guru_stats.find_transcripts(self.fx.projects, SESSION, [f"{INV}-linus", f"{INV}-guido"])
        self.assertEqual(set(found), {f"{INV}-linus"})

    def test_ignores_other_sessions(self) -> None:
        other = self.fx.projects / "-some-project" / "other-session" / "subagents"
        other.mkdir(parents=True)
        (other / "agent-alinus-x.meta.json").write_text(json.dumps({"name": f"{INV}-linus"}))
        (other / "agent-alinus-x.jsonl").write_text("")
        self.assertEqual(guru_stats.find_transcripts(self.fx.projects, SESSION, [f"{INV}-linus"]), {})

    def test_finds_session_under_a_different_project_dir(self) -> None:
        # The project dir name changes when a session enters a worktree; only the session id is stable.
        moved = self.fx.projects / "-moved-worktree" / SESSION / "subagents"
        moved.mkdir(parents=True)
        (moved / "agent-aguido-x.meta.json").write_text(json.dumps({"name": f"{INV}-guido"}))
        (moved / "agent-aguido-x.jsonl").write_text("")
        found = guru_stats.find_transcripts(self.fx.projects, SESSION, [f"{INV}-guido"])
        self.assertEqual(set(found), {f"{INV}-guido"})

    def test_skips_unreadable_meta(self) -> None:
        (self.fx.subagents / "agent-abad-x.meta.json").write_text("{not json")
        self.fx.add(f"{INV}-linus", [])
        found = guru_stats.find_transcripts(self.fx.projects, SESSION, [f"{INV}-linus"])
        self.assertEqual(set(found), {f"{INV}-linus"})


class RenderTest(unittest.TestCase):
    def stats(self, name: str) -> guru_stats.Stats:
        """Build a Stats record with fixed numbers."""
        return guru_stats.Stats(name, 1234, 56, 3, 4, 75.0, set())

    def test_table_has_requested_columns_and_drops_invocation_prefix(self) -> None:
        table = guru_stats.render([self.stats(f"{INV}-linus")], INV, {f"{INV}-linus": 4})
        header = table.splitlines()[0]
        for col in ("Teammate", "Tokens", "Sent", "Received", "Wall clock", "Contribution"):
            self.assertIn(col, header)
        row = table.splitlines()[2]
        self.assertIn("linus", row)
        self.assertNotIn(INV, row)
        self.assertIn("1,234 (56 out)", row)
        self.assertIn("1m 15s", row)
        self.assertIn("★★★★☆", row)

    def test_missing_star_rating_is_shown_as_unrated(self) -> None:
        table = guru_stats.render([self.stats(f"{INV}-linus")], INV, {})
        self.assertIn("unrated", table.splitlines()[2])

    def test_seconds_formatting(self) -> None:
        self.assertEqual(guru_stats.fmt_duration(9.4), "9s")
        self.assertEqual(guru_stats.fmt_duration(60), "1m 00s")
        self.assertEqual(guru_stats.fmt_duration(3725), "1h 02m 05s")

    def test_missing_transcript_row_is_marked(self) -> None:
        table = guru_stats.render([], INV, {}, missing=[f"{INV}-guido"])
        self.assertIn("guido", table)
        self.assertIn("no transcript", table)


class CitedByTest(unittest.TestCase):
    def test_counts_peers_whose_final_names_each_member(self) -> None:
        stats = [
            guru_stats.Stats("a", 0, 0, 0, 0, 0.0, {"b", "c"}),
            guru_stats.Stats("b", 0, 0, 0, 0, 0.0, {"c"}),
            guru_stats.Stats("c", 0, 0, 0, 0, 0.0, set()),
        ]
        self.assertEqual(guru_stats.cited_by(stats), {"a": 0, "b": 1, "c": 2})


class SignalsTest(unittest.TestCase):
    def test_signals_line_lists_citations_per_teammate_without_prefix(self) -> None:
        stats = [
            guru_stats.Stats(f"{INV}-linus", 0, 0, 0, 0, 0.0, {f"{INV}-guido"}),
            guru_stats.Stats(f"{INV}-guido", 0, 0, 0, 0, 0.0, set()),
        ]
        line = guru_stats.render_signals(stats, INV)
        self.assertIn("guido 1", line)
        self.assertIn("linus 0", line)
        self.assertNotIn(INV, line)


class StarArgTest(unittest.TestCase):
    def test_parses_and_clamps_star_pairs(self) -> None:
        stars = guru_stats.parse_stars("linus=4,guido=5", INV)
        self.assertEqual(stars, {f"{INV}-linus": 4, f"{INV}-guido": 5})

    def test_rejects_out_of_range(self) -> None:
        with self.assertRaises(ValueError):
            guru_stats.parse_stars("linus=6", INV)
        with self.assertRaises(ValueError):
            guru_stats.parse_stars("linus=0", INV)

    def test_rejects_malformed_pair(self) -> None:
        with self.assertRaises(ValueError):
            guru_stats.parse_stars("linus", INV)


if __name__ == "__main__":
    unittest.main()
