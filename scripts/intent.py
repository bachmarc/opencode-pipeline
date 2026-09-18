#!/usr/bin/env python3
"""Intent tracking script for session recovery (Story 06-02).

Deterministic intent management: start, done, show, open subcommands.
Uses only stdlib (json, argparse, pathlib, datetime).

Exit code: 0 on success, 1 on error (story not found, no open intent, etc.)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_intent_file(pipeline_dir: Path) -> Path:
    """Get the path to intent.json."""
    return pipeline_dir / "intent.json"


def load_intents(intent_file: Path) -> dict:
    """Load intents from JSON file."""
    if not intent_file.exists():
        return {"intents": []}
    
    try:
        with open(intent_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"intents": []}


def save_intents(intent_file: Path, data: dict) -> None:
    """Save intents to JSON file."""
    intent_file.parent.mkdir(parents=True, exist_ok=True)
    with open(intent_file, "w") as f:
        json.dump(data, f, indent=2)


def cmd_start(
    args: argparse.Namespace,
) -> int:
    """Start a new intent.
    
    Args: story_id, agent, step, [--worktree], [--branch]
    Returns: 0 on success, 1 on error
    """
    pipeline_dir = Path(args.pipeline_dir)
    intent_file = get_intent_file(pipeline_dir)
    
    data = load_intents(intent_file)
    
    intent = {
        "story_id": args.story_id,
        "agent": args.agent,
        "step": args.step,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "done": False,
    }
    
    # Add optional fields if provided
    if args.worktree:
        intent["worktree"] = args.worktree
    if args.branch:
        intent["branch"] = args.branch
    
    data["intents"].append(intent)
    save_intents(intent_file, data)
    
    return 0


def cmd_done(
    args: argparse.Namespace,
) -> int:
    """Mark the latest open intent for a story as done.
    
    Args: story_id
    Returns: 0 on success, 1 if story not found or no open intent
    """
    pipeline_dir = Path(args.pipeline_dir)
    intent_file = get_intent_file(pipeline_dir)
    
    data = load_intents(intent_file)
    
    # Find the latest open intent for this story
    for intent in reversed(data["intents"]):
        if intent["story_id"] == args.story_id and not intent["done"]:
            intent["done"] = True
            save_intents(intent_file, data)
            return 0
    
    # Story not found or no open intent
    return 1


def cmd_show(
    args: argparse.Namespace,
) -> int:
    """Show all intents as JSON.
    
    Returns: 0 on success
    """
    pipeline_dir = Path(args.pipeline_dir)
    intent_file = get_intent_file(pipeline_dir)
    
    data = load_intents(intent_file)
    
    # Output intents as JSON list to stdout
    print(json.dumps(data["intents"], indent=2))
    
    return 0


def cmd_open(
    args: argparse.Namespace,
) -> int:
    """Show only open (not-done) intents as JSON.
    
    Returns: 0 on success
    """
    pipeline_dir = Path(args.pipeline_dir)
    intent_file = get_intent_file(pipeline_dir)
    
    data = load_intents(intent_file)
    
    # Filter to only open intents
    open_intents = [i for i in data["intents"] if not i["done"]]
    
    # Output as JSON list to stdout
    print(json.dumps(open_intents, indent=2))
    
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Intent tracking for session recovery"
    )
    
    parser.add_argument(
        "--pipeline-dir",
        type=str,
        default=".pipeline",
        help="Path to .pipeline directory (default: .pipeline)",
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # start subcommand
    start_parser = subparsers.add_parser("start", help="Start a new intent")
    start_parser.add_argument("story_id", help="Story ID (e.g., 06-01)")
    start_parser.add_argument("agent", help="Agent name (e.g., developer)")
    start_parser.add_argument("step", help="Step description")
    start_parser.add_argument("--worktree", help="Worktree path (optional)")
    start_parser.add_argument("--branch", help="Branch name (optional)")
    start_parser.set_defaults(func=cmd_start)
    
    # done subcommand
    done_parser = subparsers.add_parser("done", help="Mark intent as done")
    done_parser.add_argument("story_id", help="Story ID (e.g., 06-01)")
    done_parser.set_defaults(func=cmd_done)
    
    # show subcommand
    show_parser = subparsers.add_parser("show", help="Show all intents")
    show_parser.set_defaults(func=cmd_show)
    
    # open subcommand
    open_parser = subparsers.add_parser("open", help="Show open intents")
    open_parser.set_defaults(func=cmd_open)
    
    args = parser.parse_args()
    
    try:
        return args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
