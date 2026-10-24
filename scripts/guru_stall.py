#!/usr/bin/env python3
"""Stall detector for tao guru-chat's live roundtable.

Polls the lead's inbox for FINAL POSITION report-outs and idle notifications, emitting
PROGRESS/STALL/PREMATURE/ALL_REPORTED lines for a Monitor to watch. Every protocol message
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HEADER = re.compile(r"\[RT:(?P<inv>[^|\]]+)\|(?P<type>[A-Z]+)\|r(?P<round>\d+)\]")
ENGAGED = re.compile(r"^PEERS ENGAGED:[ \t]*(?P<names>.*)$", re.MULTILINE)
CHANGED = re.compile(r"^CHANGED:[ \t]*\S", re.MULTILINE)
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


def _engages_peer(text: str, sender: str, invocation: str, roster: list[str]) -> bool:
    match = ENGAGED.search(text)
    if not match:
        return False
    named = {t.strip().lower() for t in re.split(r"[,;\s]+", match.group("names")) if t.strip()}
    for peer in roster:
        if peer == sender:
            continue
        if peer.lower() in named or _short(peer, invocation).lower() in named:
            return True
    return False


def classify(messages: list[dict[str, Any]], invocation: str, roster: list[str], min_round: int) -> Report:
    """Classify inbox messages for one roundtable invocation.

    Only roster senders and messages headed with this invocation id count. A sender is
    `accepted` once any of its FINAL messages meets the round and engagement rules; a sender
    with only non-conforming FINALs is `premature`.
    """
    members = set(roster)
    accepted: set[str] = set()
    flagged: set[str] = set()
    reported_or_flagged: set[str] = set()
    idle: set[str] = set()
    for msg in messages:
        sender = msg.get("from", "")
        if sender not in members:
            continue
        text = msg.get("text", "")
        if "idle_notification" in text:
            idle.add(sender)
            continue
        header = HEADER.search(text)
        if not header or header["inv"] != invocation or header["type"] != "FINAL":
            continue
        reported_or_flagged.add(sender)
        ok = (
            int(header["round"]) >= min_round
            and _engages_peer(text, sender, invocation, roster)
            and CHANGED.search(text) is not None
        )
        (accepted if ok else flagged).add(sender)
    return Report(
        accepted=sorted(accepted),
        premature=sorted(flagged - accepted),
        idle_unreported=sorted(idle - reported_or_flagged),
    )


def poll(inbox: Path, invocation: str, roster: list[str], min_round: int) -> None:
    """Poll until every roster member has an accepted FINAL, printing events for a Monitor."""
    n = len(roster)
    prev: tuple[int, int] = (-1, -1)
    quiet = 0
    while True:
        messages: list[dict[str, Any]] = []
        if inbox.exists():
            try:
                messages = json.loads(inbox.read_text())
            except (OSError, json.JSONDecodeError):
                # A concurrent write can leave the file mid-write; skip this poll rather
                # than treating it as an empty inbox, which would regress the counts.
                time.sleep(POLL_SECONDS)
                continue
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
            break
        if quiet >= STALL_SECONDS:
            print(
                f"STALL reported={state[0]}/{n} idle_not_reported=[{','.join(report.idle_unreported)}]",
                flush=True,
            )
            quiet = 0
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    poll(
        inbox_path(sys.argv[1]),
        sys.argv[2],
        [r for r in sys.argv[3].split(",") if r],
        int(sys.argv[4]) if len(sys.argv) > 4 else 3,
    )
