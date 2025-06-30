#!/usr/bin/env python3
"""
analysis.py

Load data-center-specific patterns (with issue_type and steps),
match them against pasted logs (case-insensitive), and also
catch any generic ERROR lines for online fallback.
"""
import re
import json
from db import load_db

# Load your extended logs_db.json
with open("logs_db.json", "r") as f:
    PATTERNS = json.load(f)

# Load any overrides the user has saved
OVERRIDES = load_db()


def analyze(log_text):
    """
    Scan log_text for known patterns (case-insensitive),
    then catch any generic ERROR:<message> lines as fallback entries.
    Returns a list of dicts, each with:
      - pattern
      - issue_type
      - fix (override or default_fix, or empty for ERROR lines)
      - steps (list)
    """
    matches = []

    # 1) Data-center-specific patterns
    for entry in PATTERNS:
        if re.search(entry["pattern"], log_text, re.IGNORECASE):
            fix = OVERRIDES.get(entry["pattern"], entry["default_fix"])
            matches.append({
                "pattern":    entry["pattern"],
                "issue_type": entry["issue_type"],
                "fix":        fix,
                "steps":      entry.get("steps", []),
            })

    # 2) Generic ERROR:<message> fallback
    for line in log_text.splitlines():
        m = re.match(r".*ERROR[:\s]+(.+)", line, re.IGNORECASE)
        if m:
            err_msg = m.group(1).strip()
            # Only add if not already matched by a specific pattern
            if not any(d["pattern"].lower() == err_msg.lower() for d in matches):
                matches.append({
                    "pattern":    err_msg,
                    "issue_type": "Unknown Error (Online Research)",
                    "fix":        OVERRIDES.get(err_msg, ""),
                    "steps":      [],  # no built-in steps
                })

    return matches
