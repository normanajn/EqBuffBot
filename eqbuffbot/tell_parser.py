"""Parse EverQuest log lines into TellEvent objects."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Format: [Sun Mar 08 12:34:56 2026] SenderName tells you, 'message'
_TELL_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\] "
    r"(?P<sender>\S+) tells you, '(?P<message>.+)'$"
)

_TIMESTAMP_FORMAT = "%a %b %d %H:%M:%S %Y"


@dataclass
class TellEvent:
    timestamp: datetime
    sender: str
    message: str


def parse_line(line: str, character_name: str) -> Optional[TellEvent]:
    """Return a TellEvent if the line is an incoming tell, otherwise None."""
    line = line.strip()
    m = _TELL_RE.match(line)
    if not m:
        return None

    try:
        ts = datetime.strptime(m.group("timestamp"), _TIMESTAMP_FORMAT)
    except ValueError:
        return None

    return TellEvent(
        timestamp=ts,
        sender=m.group("sender"),
        message=m.group("message"),
    )
