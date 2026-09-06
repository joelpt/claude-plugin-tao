#!/usr/bin/env python3
"""Stall detector for tao guru-chat's live team roundtable.

Polls a team's team-lead inbox for FINAL POSITION report-outs and idle
notifications, emitting PROGRESS/STALL/ALL_REPORTED lines for a Monitor
to watch. Purely argv-driven (team name, expected voice count) — no
per-invocation templating needed, so this file is shipped once and
invoked directly rather than regenerated into /tmp per team.

Usage: python3 guru_stall.py <team-name> <expected-voice-count>
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


def poll(team: str, n: int) -> None:
    """Poll a team's inbox until every voice has reported or the caller exits.

    Args:
        team: Team name whose team-lead inbox to watch.
        n: Expected number of voices that must send a FINAL POSITION.

    """
    lead: Path = Path.home() / ".claude" / "teams" / team / "inboxes" / "team-lead.json"
    prev: int = -1
    quiet: int = 0

    while True:
        messages: list[dict[str, Any]] = []
        if lead.exists():
            try:
                messages = json.loads(lead.read_text())
            except (OSError, json.JSONDecodeError):
                # A concurrent write can leave the file mid-write; skip this
                # poll rather than treating it as an empty inbox, which would
                # otherwise regress `done`/`cnt` back to zero.
                time.sleep(15)
                continue

        done = sorted(
            {
                x.get("from", "")
                for x in messages
                if "FINAL POSITION" in x.get("text", "")
                and "idle_notification" not in x.get("text", "")
            }
        )
        idle = sorted(
            {
                x.get("from", "")
                for x in messages
                if "idle_notification" in x.get("text", "") and x.get("from", "") not in done
            }
        )
        cnt = len(done)
        if cnt != prev:
            print(f"PROGRESS reported={cnt}/{n} [{','.join(done)}]", flush=True)
            prev = cnt
            quiet = 0
        else:
            quiet += 15
        if cnt >= n:
            print(f"ALL_REPORTED [{','.join(done)}]", flush=True)
            break
        if quiet >= 90:
            print(f"STALL reported={cnt}/{n} idle_not_reported=[{','.join(idle)}]", flush=True)
            quiet = 0
        time.sleep(15)


if __name__ == "__main__":
    poll(sys.argv[1], int(sys.argv[2]))
