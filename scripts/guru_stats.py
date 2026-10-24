#!/usr/bin/env python3
"""Per-teammate statistics table for tao guru-chat's live roundtable.

Reads each roster member's subagent transcript (located by session id and the agent name in its
`.meta.json`, since the project directory name changes when a session enters a worktree) and
reports tokens, messages sent and received, wall-clock time and a star rating for contribution.
Only the star rating is a judgment: the lead passes it in with `--stars`.

Usage: python3 guru_stats.py <session-id> <invocation-id> <roster-csv> [--stars linus=4,guido=3] [--projects-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from guru_stall import ENGAGED, HEADER

MAIL = re.compile(r"<teammate-message\b(?P<attrs>[^>]*)>(?P<body>.*?)</teammate-message>", re.DOTALL)
SENDER = re.compile(r'teammate_id="(?P<sender>[^"]*)"')
Row = dict[str, object]


@dataclass
class Stats:
    """One teammate's roundtable statistics.

    Attributes:
        name: Full roster name, including the invocation prefix.
        tokens_total: Input, cache-creation, cache-read and output tokens summed over all turns.
        tokens_output: Output tokens only.
        sent: Plain-text messages sent with SendMessage.
        received: Plain-text teammate messages received, excluding the spawn prompt.
        seconds: Seconds from the first to the last transcript row.
        engaged: Roster members named under `PEERS ENGAGED:` in the teammate's last FINAL.
    """

    name: str
    tokens_total: int
    tokens_output: int
    sent: int
    received: int
    seconds: float
    engaged: set[str]


def _short(name: str, invocation: str) -> str:
    prefix = f"{invocation}-"
    return name[len(prefix) :] if name.startswith(prefix) else name


def _token(raw: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", raw.strip().lstrip("@").lower())


def _read_rows(path: Path) -> list[Row]:
    rows: list[Row] = []
    for line in path.read_text().splitlines():
        try:
            parsed = json.loads(line)
        except ValueError:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def find_transcripts(projects_dir: Path, session_id: str, roster: list[str]) -> dict[str, Path]:
    """Map each roster name to its subagent transcript for the session.

    Args:
        projects_dir: Claude Code projects directory (`~/.claude/projects`).
        session_id: Current session id; the only stable key across worktree moves.
        roster: Full teammate names to look for.

    Returns:
        Transcript path per roster name found. When a name was spawned twice the newest wins.
    """
    found: dict[str, Path] = {}
    metas = sorted(projects_dir.glob(f"*/{session_id}/subagents/*.meta.json"), key=lambda p: p.stat().st_mtime)
    for meta in metas:
        try:
            name = json.loads(meta.read_text()).get("name")
        except (ValueError, AttributeError):
            continue
        transcript = meta.with_name(meta.name.removesuffix(".meta.json") + ".jsonl")
        if name in roster and transcript.exists():
            found[name] = transcript
    return found


def _usage_totals(rows: list[Row]) -> tuple[int, int]:
    best: dict[str, tuple[int, int]] = {}
    for row in rows:
        message = row.get("message")
        if row.get("type") != "assistant" or not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        out = int(usage.get("output_tokens", 0))
        total = out + sum(int(usage.get(k, 0)) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        key = str(message.get("id") or id(row))
        if key not in best or total > best[key][0]:
            best[key] = (total, out)
    return sum(t for t, _ in best.values()), sum(o for _, o in best.values())


def _sent_messages(rows: list[Row]) -> list[str]:
    seen: set[str] = set()
    texts: list[str] = []
    for row in rows:
        message = row.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if row.get("type") != "assistant" or not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("name") != "SendMessage" or block.get("id") in seen:
                continue
            seen.add(str(block.get("id")))
            payload = block.get("input")
            body = payload.get("message") if isinstance(payload, dict) else None
            if isinstance(body, str):
                texts.append(body)
    return texts


def _user_text(row: Row) -> str:
    message = row.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(b.get("text", "")) for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _is_protocol_frame(body: str) -> bool:
    try:
        parsed, _ = json.JSONDecoder().raw_decode(body.strip())
    except ValueError:
        return False
    return isinstance(parsed, dict) and "type" in parsed


def _received_count(rows: list[Row]) -> int:
    mails = [m for row in rows if row.get("type") == "user" for m in MAIL.finditer(_user_text(row))]
    if mails:
        first = SENDER.search(mails[0].group("attrs"))
        if first and first.group("sender") == "team-lead":
            mails = mails[1:]
    return sum(1 for m in mails if not _is_protocol_frame(m.group("body")))


def _seconds(rows: list[Row]) -> float:
    stamps = [datetime.fromisoformat(str(r["timestamp"]).replace("Z", "+00:00")) for r in rows if isinstance(r.get("timestamp"), str)]
    return (max(stamps) - min(stamps)).total_seconds() if stamps else 0.0


def _engaged(sent: list[str], name: str, roster: list[str]) -> set[str]:
    finals = [t for t in sent if (m := HEADER.search(t)) and m.group("type") == "FINAL"]
    match = ENGAGED.search(finals[-1]) if finals else None
    if not match:
        return set()
    named = {_token(t) for t in re.split(r"[,;\s]+", match.group("names"))} - {""}
    return {p for p in roster if p != name and any(p == t or p.endswith(f"-{t}") for t in named)}


def analyze(name: str, path: Path, roster: list[str]) -> Stats:
    """Compute one teammate's statistics from its transcript.

    Args:
        name: Full roster name of the teammate.
        path: Path to its subagent transcript.
        roster: Full names of every roundtable member, used to resolve `PEERS ENGAGED:`.

    Returns:
        The teammate's Stats.
    """
    rows = _read_rows(path)
    total, output = _usage_totals(rows)
    sent = _sent_messages(rows)
    return Stats(name, total, output, len(sent), _received_count(rows), _seconds(rows), _engaged(sent, name, roster))


def cited_by(stats: list[Stats]) -> dict[str, int]:
    """Count how many peers' FINAL positions name each teammate under `PEERS ENGAGED:`."""
    return {s.name: sum(1 for other in stats if s.name in other.engaged) for s in stats}


def fmt_duration(seconds: float) -> str:
    """Format seconds as `9s`, `1m 05s` or `1h 02m 05s`."""
    whole = int(seconds)
    hours, rest = divmod(whole, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def parse_stars(spec: str, invocation: str) -> dict[str, int]:
    """Parse `linus=4,guido=5` into ratings keyed by full roster name.

    Args:
        spec: Comma-separated `name=stars` pairs, stars from 1 to 5.
        invocation: Invocation id; added as a prefix to names that lack it.

    Returns:
        Star rating per full roster name.

    Raises:
        ValueError: If a pair is malformed or its rating is outside 1-5.
    """
    stars: dict[str, int] = {}
    for pair in filter(None, (p.strip() for p in spec.split(","))):
        name, sep, value = pair.partition("=")
        if not sep or not value.strip().isdigit() or not 1 <= int(value) <= 5:
            raise ValueError(f"bad star rating {pair!r}: expected name=1..5")
        key = name.strip()
        stars[key if key.startswith(f"{invocation}-") else f"{invocation}-{key}"] = int(value)
    return stars


def render(stats: list[Stats], invocation: str, stars: dict[str, int], missing: list[str] | None = None) -> str:
    """Render the statistics as a markdown table.

    Args:
        stats: One Stats per teammate with a transcript.
        invocation: Invocation id, dropped from displayed names.
        stars: Star rating per full roster name; absent names show as unrated.
        missing: Roster names with no transcript.

    Returns:
        The markdown table.
    """
    lines = [
        "| Teammate | Tokens (total) | Sent | Received | Wall clock | Contribution |",
        "|---|---|---|---|---|---|",
    ]
    for s in stats:
        rating = stars.get(s.name)
        shown = "★" * rating + "☆" * (5 - rating) if rating else "unrated"
        lines.append(
            f"| {_short(s.name, invocation)} | {s.tokens_total:,} ({s.tokens_output:,} out) | {s.sent} | {s.received} "
            f"| {fmt_duration(s.seconds)} | {shown} |"
        )
    for name in missing or []:
        lines.append(f"| {_short(name, invocation)} | no transcript found | - | - | - | unrated |")
    return "\n".join(lines)


def render_signals(stats: list[Stats], invocation: str) -> str:
    """Render the peer-citation counts the lead weighs when rating contribution."""
    counts = cited_by(stats)
    return "Cited by peers' FINALs: " + ", ".join(f"{_short(n, invocation)} {c}" for n, c in counts.items())


def main(argv: list[str]) -> int:
    """Print the statistics table for a roundtable.

    Args:
        argv: Command-line arguments after the program name.

    Returns:
        Process exit code: 0 on success, 2 on invalid arguments.
    """
    parser = argparse.ArgumentParser(description="Per-teammate roundtable statistics")
    parser.add_argument("session_id")
    parser.add_argument("invocation")
    parser.add_argument("roster_csv")
    parser.add_argument("--stars", default="")
    parser.add_argument("--projects-dir", default=os.environ.get("CLAUDE_PROJECTS_DIR", str(Path.home() / ".claude" / "projects")))
    args = parser.parse_args(argv)
    try:
        stars = parse_stars(args.stars, args.invocation)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    roster = [n.strip() for n in args.roster_csv.split(",") if n.strip()]
    found = find_transcripts(Path(args.projects_dir), args.session_id, roster)
    stats = [analyze(n, found[n], roster) for n in roster if n in found]
    print(render(stats, args.invocation, stars, [n for n in roster if n not in found]))
    if not stars:
        print()
        print(render_signals(stats, args.invocation))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
