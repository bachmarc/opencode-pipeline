#!/usr/bin/env python3
"""QA verdict routing with budget tracking.

Manages verdict history in .pipeline/qa-state/<story-id>.json and determines
next action based on verdict counts and budget limits:
- 3 FAILs → blocked-requirements
- 2 BLOCKED_Design → blocked-requirements

Schema: {"verdicts": [{"verdict": "PASS"|"FAIL"|"BLOCKED_Design", "timestamp": "…", …}]}

Usage:
  qa_route.py record <story-id> <verdict>  # Record a verdict (PASS, FAIL, BLOCKED_Design, etc.)
  qa_route.py next <story-id>              # Get next action based on history
  qa_route.py history <story-id>           # Get full verdict history

Exit codes:
  0 - Success
  1 - Story not found (for 'next' and 'history' commands)
  
Output: JSON to stdout
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def get_repo_root() -> Path:
    """Find repo root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_qa_state_file(story_id: str) -> Path:
    """Get path to qa-state file for a story."""
    repo_root = get_repo_root()
    qa_state_dir = repo_root / ".pipeline" / "qa-state"
    qa_state_dir.mkdir(parents=True, exist_ok=True)
    return qa_state_dir / f"{story_id}.json"


def load_state(story_id: str) -> dict[str, Any]:
    """Load verdict history for a story."""
    state_file = get_qa_state_file(story_id)
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {"verdicts": []}


def save_state(story_id: str, state: dict[str, Any]) -> None:
    """Save verdict history for a story."""
    state_file = get_qa_state_file(story_id)
    state_file.write_text(json.dumps(state, indent=2))


def record_verdict(story_id: str, verdict: str) -> None:
    """Record a verdict for a story."""
    state = load_state(story_id)
    
    # Add new verdict with timestamp
    state["verdicts"].append({
        "verdict": verdict,
        "timestamp": datetime.now(UTC).isoformat(),
    })
    
    save_state(story_id, state)
    
    # Output confirmation
    print(json.dumps({
        "recorded": True,
        "story_id": story_id,
        "verdict": verdict,
        "count": len(state["verdicts"]),
    }))


def get_next_action(story_id: str) -> dict[str, Any]:
    """Determine next action based on verdict history."""
    state = load_state(story_id)
    verdicts = state.get("verdicts", [])
    
    if not verdicts:
        return {
            "action": "unknown",
            "reason": "No verdicts recorded",
        }
    
    # Count verdicts by type
    fail_count = sum(1 for v in verdicts if v["verdict"] == "FAIL")
    blocked_design_count = sum(1 for v in verdicts if v["verdict"] == "BLOCKED_Design")
    
    # Get last verdict
    last_verdict = verdicts[-1]["verdict"]
    
    # Determine action based on counts and budget limits
    if last_verdict == "PASS":
        return {
            "action": "documenter",
            "branch": story_id,
        }
    
    # Check FAIL budget (3 FAILs → blocked)
    if fail_count >= 3:
        return {
            "action": "blocked-requirements",
            "fail_count": fail_count,
            "reason": "FAIL budget exceeded (3 limit)",
        }
    
    if last_verdict == "FAIL":
        return {
            "action": "developer-fix",
            "branch": story_id,
            "fail_count": fail_count,
        }
    
    # Check BLOCKED_Design budget (2 → blocked)
    if blocked_design_count >= 2:
        return {
            "action": "blocked-requirements",
            "design_fix_count": blocked_design_count,
            "reason": "BLOCKED_Design budget exceeded (2 limit)",
        }
    
    if last_verdict == "BLOCKED_Design":
        return {
            "action": "architect-fix",
            "branch": story_id,
            "design_fix_count": blocked_design_count,
        }
    
    # Default
    return {
        "action": "unknown",
        "last_verdict": last_verdict,
    }


def get_history(story_id: str) -> dict[str, Any]:
    """Get full verdict history for a story."""
    state = load_state(story_id)
    return state


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="QA verdict routing with budget tracking"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # record subcommand
    record_parser = subparsers.add_parser("record", help="Record a verdict")
    record_parser.add_argument("story_id", help="Story ID (e.g., 06-11)")
    record_parser.add_argument("verdict", help="Verdict (PASS, FAIL, BLOCKED_Design, etc.)")
    
    # next subcommand
    next_parser = subparsers.add_parser("next", help="Get next action")
    next_parser.add_argument("story_id", help="Story ID (e.g., 06-11)")
    
    # history subcommand
    history_parser = subparsers.add_parser("history", help="Get verdict history")
    history_parser.add_argument("story_id", help="Story ID (e.g., 06-11)")
    
    args = parser.parse_args()
    
    try:
        if args.command == "record":
            record_verdict(args.story_id, args.verdict)
            return 0
        
        elif args.command == "next":
            action = get_next_action(args.story_id)
            print(json.dumps(action))
            return 0
        
        elif args.command == "history":
            history = get_history(args.story_id)
            print(json.dumps(history))
            return 0
        
        return 1
    
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
