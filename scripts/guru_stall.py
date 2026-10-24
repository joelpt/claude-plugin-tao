#!/usr/bin/env python3
"""Stall detector for tao guru-chat's live roundtable.

Polls the lead's inbox for FINAL POSITION report-outs and idle notifications, emitting
PROGRESS/STALL/PREMATURE/INBOX_MISSING/INBOX_INVALID/ALL_REPORTED lines for a Monitor to watch. Every protocol message
carries an invocation-scoped header, `[RT:<invocation>|<TYPE>|r<round>]`, and only messages
from the invocation's own roster are considered, so a second roundtable in the same session
or an unrelated teammate cannot be miscounted. A FINAL is accepted only when its round is at
least `min_round`, it names at least one roster peer other than the sender under
`PEERS ENGAGED:`, and it states a `CHANGED:` line.

Usage: python3 guru_stall.py <inbox-json-path|team-name> <invocation-id> <roster-csv> [min-round]
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HEADER = re.compile(r"\[RT:(?P<inv>[^|\]]+)\|(?P<type>[A-Z]+)\|r(?P<round>\d+)\]")
_LABEL_PREFIX = r"^[ \t>*_\-\u2022#]*"
ENGAGED = re.compile(_LABEL_PREFIX + r"PEERS ENGAGED[*_ \t]*:[*_ \t]*(?P<names>.*)$", re.MULTILINE)
CHANGED = re.compile(_LABEL_PREFIX + r"CHANGED[*_ \t]*:[*_ \t]*\S", re.MULTILINE)
POLL_SECONDS = 15
STALL_SECONDS = 90


@dataclass
class Report:
    accepted: list[str] = field(default_factory=list)
    premature: list[str] = field(default_factory=list)
    idle_unreported: list[str] = field(default_factory=list)


def inbox_path(arg: str) -> Path:
    """Resolve the lead inbox: an explicit .json path, else a team name under ~/.claude/teams."""
    if arg.endswith(".json"):
        return Path(arg)
    return Path.home() / ".claude" / "teams" / arg / "inboxes" / "team-lead.json"


def _short(name: str, invocation: str) -> str:
    prefix = f"{invocation}-"
    return name[len(prefix):] if name.startswith(prefix) else name


def _token(raw: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", raw.strip().lstrip("@").lower())


def _engages_peer(text: str, sender: str, invocation: str, roster: list[str]) -> bool:
    match = ENGAGED.search(text)
    if not match:
        return False
    named = {_token(t) for t in re.split(r"[,;\s]+", match.group("names"))} - {""}
    for peer in roster:
        if peer == sender:
            continue
        if _token(peer) in named or _token(_short(peer, invocation)) in named:
            return True
    return False


def _is_idle(text: str) -> bool:
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return "idle_notification" in text
    return isinstance(parsed, dict) and parsed.get("type") == "idle_notification"


def classify(messages: list[Any], invocation: str, roster: list[str], min_round: int) -> Report:
    """Classify inbox messages for one roundtable invocation.

    Only roster senders and messages headed with this invocation id count as reports. A sender
    is `accepted` once any of its FINAL messages meets the round and engagement rules; a sender
    with only non-conforming FINALs is `premature`. `idle_unreported` lists non-accepted senders
    whose latest message is an idle notification or a non-conforming FINAL, i.e. who are stuck.
    """
    members = set(roster)
    accepted: set[str] = set()
    flagged: set[str] = set()
    last_kind: dict[str, str] = {}
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        sender = msg.get("from", "")
        if sender not in members:
            continue
        text = msg.get("text", "")
        if not isinstance(text, str):
            continue
        header = HEADER.search(text)
        if header is None:
            if _is_idle(text):
                last_kind[sender] = "idle"
            continue
        if header["inv"] != invocation:
            continue
        if header["type"] != "FINAL":
            last_kind[sender] = "other"
            continue
        ok = (
            int(header["round"]) >= min_round
            and _engages_peer(text, sender, invocation, roster)
            and CHANGED.search(text) is not None
        )
        if ok:
            accepted.add(sender)
        else:
            flagged.add(sender)
        last_kind[sender] = "ok" if ok else "bad"
    stuck = {s for s, k in last_kind.items() if k in ("idle", "bad")} - accepted
    return Report(
        accepted=sorted(accepted),
        premature=sorted(flagged - accepted),
        idle_unreported=sorted(stuck),
    )


def poll(
    inbox: Path,
    invocation: str,
    roster: list[str],
    min_round: int,
    sleep: Callable[[float], None] = time.sleep,
    max_polls: int | None = None,
) -> None:
    """Poll until every roster member has an accepted FINAL, printing events for a Monitor."""
    n = len(roster)
    prev: tuple[int, int] = (-1, -1)
    quiet = 0
    warned: set[str] = set()
    polls = 0
    while max_polls is None or polls < max_polls:
        polls += 1
        messages: list[Any] = []
        if not inbox.exists():
            if "missing" not in warned:
                print(f"INBOX_MISSING {inbox}", flush=True)
                warned.add("missing")
        else:
            warned.discard("missing")
            try:
                loaded = json.loads(inbox.read_text())
            except (OSError, json.JSONDecodeError):
                # A concurrent write can leave the file mid-write; skip this poll rather
                # than treating it as an empty inbox, which would regress the counts.
                sleep(POLL_SECONDS)
                continue
            if isinstance(loaded, list):
                messages = loaded
                warned.discard("invalid")
            elif "invalid" not in warned:
                print(f"INBOX_INVALID {inbox} is not a JSON list", flush=True)
                warned.add("invalid")
        report = classify(messages, invocation, roster, min_round)
        state = (len(report.accepted), len(report.premature))
        if state != prev:
            print(f"PROGRESS reported={state[0]}/{n} [{','.join(report.accepted)}]", flush=True)
            if report.premature:
                print(f"PREMATURE [{','.join(report.premature)}]", flush=True)
            prev = state
            quiet = 0
        else:
            quiet += POLL_SECONDS
        if state[0] >= n:
            print(f"ALL_REPORTED [{','.join(report.accepted)}]", flush=True)
            return
        if quiet >= STALL_SECONDS:
            print(
                f"STALL reported={state[0]}/{n} stuck=[{','.join(report.idle_unreported)}]",
                flush=True,
            )
            quiet = 0
        sleep(POLL_SECONDS)


if __name__ == "__main__":
    poll(
        inbox_path(sys.argv[1]),
        sys.argv[2],
        [r for r in sys.argv[3].split(",") if r],
        int(sys.argv[4]) if len(sys.argv) > 4 else 3,
    )
