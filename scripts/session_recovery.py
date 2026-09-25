#!/usr/bin/env python3
"""Session recovery script for pipeline state collection (Story 06-08).

Pulls latest changes from remote before scanning state (Story 19-02).
Collects comprehensive pipeline state: open intents, worktrees, main state,
QA state, and feature claims. Outputs JSON to stdout and human-readable
summary to stderr.

Uses only stdlib + git subprocess. No external dependencies.

Exit code: 0 on success, 1 if recovery items exist (with --check flag).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_git_command(
    args: list[str], cwd: Path, check: bool = False
) -> tuple[int, str, str]:
    """Run a git command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 1, "", "git not found"


def load_json_file(path: Path) -> dict | list:
    """Load JSON file, return empty dict/list on error."""
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def get_open_intents(pipeline_dir: Path) -> list[dict]:
    """Get open intents from .pipeline/intent.json."""
    intent_file = pipeline_dir / "intent.json"
    data = load_json_file(intent_file)
    
    if isinstance(data, dict) and "intents" in data:
        intents = data["intents"]
        if isinstance(intents, list):
            return [i for i in intents if isinstance(i, dict) and not i.get("done", False)]
    
    return []


def get_worktree_status(worktree_path: Path) -> dict[str, Any]:
    """Get status of a single worktree."""
    status_dict: dict[str, Any] = {
        "path": str(worktree_path.relative_to(worktree_path.parent.parent)),
        "branch": "unknown",
        "uncommitted_files": [],
        "staged_files": [],
        "merge_conflicts": False,
        "detached_head": False,
    }
    
    # Get current branch
    exit_code, branch, _ = run_git_command(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        worktree_path,
    )
    if exit_code == 0:
        status_dict["branch"] = branch
        if branch == "HEAD":
            status_dict["detached_head"] = True
    
    # Get status (uncommitted and staged files)
    exit_code, status_output, _ = run_git_command(
        ["status", "--porcelain"],
        worktree_path,
    )
    if exit_code == 0:
        for line in status_output.split("\n"):
            if not line:
                continue
            status_code = line[:2]
            filename = line[3:]
            
            # Check for merge conflicts (UU, AA, DD, etc.)
            if status_code[0] == "U" or status_code[1] == "U":
                status_dict["merge_conflicts"] = True
            
            # Staged files (first character is not space)
            if status_code[0] != " ":
                status_dict["staged_files"].append(filename)
            
            # Uncommitted files (second character is not space)
            if status_code[1] != " ":
                status_dict["uncommitted_files"].append(filename)
    
    return status_dict


def get_worktrees(repo_path: Path) -> list[dict]:
    """Get all worktrees from .worktrees/ directory."""
    worktrees_dir = repo_path / ".worktrees"
    if not worktrees_dir.exists():
        return []
    
    worktrees = []
    for worktree_path in worktrees_dir.iterdir():
        if worktree_path.is_dir() and (worktree_path / ".git").exists():
            worktrees.append(get_worktree_status(worktree_path))
    
    return worktrees


def get_main_state(repo_path: Path) -> dict[str, Any]:
    """Get main branch state: ahead/behind remote, dirty."""
    state: dict[str, Any] = {
        "ahead": 0,
        "behind": 0,
        "dirty": False,
    }
    
    # Check if working tree is dirty
    exit_code, status_output, _ = run_git_command(
        ["status", "--porcelain"],
        repo_path,
    )
    if exit_code == 0 and status_output:
        state["dirty"] = True
    
    # Get ahead/behind counts
    exit_code, output, _ = run_git_command(
        ["rev-list", "--left-right", "--count", "HEAD...@{u}"],
        repo_path,
    )
    if exit_code == 0:
        parts = output.split()
        if len(parts) == 2:
            try:
                state["ahead"] = int(parts[0])
                state["behind"] = int(parts[1])
            except ValueError:
                pass
    
    return state


def get_qa_state(pipeline_dir: Path) -> dict[str, dict]:
    """Get QA state from .pipeline/qa-state/*.json files."""
    qa_state_dir = pipeline_dir / "qa-state"
    qa_state: dict[str, dict] = {}
    
    if not qa_state_dir.exists():
        return qa_state
    
    for qa_file in qa_state_dir.glob("*.json"):
        story_id = qa_file.stem
        data = load_json_file(qa_file)
        if isinstance(data, dict):
            qa_state[story_id] = data
    
    return qa_state


def get_feature_claims(repo_path: Path) -> list[dict]:
    """Get feature claims from docs/features/*/feature.md files."""
    claims = []
    features_dir = repo_path / "docs" / "features"
    
    if not features_dir.exists():
        return claims
    
    for feature_dir in features_dir.iterdir():
        if not feature_dir.is_dir():
            continue
        
        feature_file = feature_dir / "feature.md"
        if not feature_file.exists():
            continue
        
        try:
            content = feature_file.read_text()
            
            # Parse YAML frontmatter
            if content.startswith("---"):
                lines = content.split("\n")
                end_idx = None
                for i in range(1, len(lines)):
                    if lines[i].startswith("---"):
                        end_idx = i
                        break
                
                if end_idx:
                    frontmatter = "\n".join(lines[1:end_idx])
                    
                    # Simple YAML parsing for owner and status
                    owner = ""
                    status = ""
                    feature_id = ""
                    
                    for line in frontmatter.split("\n"):
                        if line.startswith("owner:"):
                            owner = line.split(":", 1)[1].strip().strip('"\'')
                        elif line.startswith("status:"):
                            status = line.split(":", 1)[1].strip().strip('"\'')
                        elif line.startswith("id:"):
                            feature_id = line.split(":", 1)[1].strip().strip('"\'')
                    
                    # Only add if claimed (owner is not empty)
                    if owner and owner != '""':
                        claims.append({
                            "feature": feature_id or feature_dir.name,
                            "owner": owner,
                            "status": status,
                        })
        except (OSError, UnicodeDecodeError):
            pass
    
    return claims


def collect_state(repo_path: Path) -> dict[str, Any]:
    """Collect all pipeline state."""
    pipeline_dir = repo_path / ".pipeline"
    
    return {
        "open_intents": get_open_intents(pipeline_dir),
        "worktrees": get_worktrees(repo_path),
        "main_state": get_main_state(repo_path),
        "qa_state": get_qa_state(pipeline_dir),
        "feature_claims": get_feature_claims(repo_path),
    }


def has_recovery_items(state: dict[str, Any]) -> bool:
    """Check if there are any recovery items (open intents or dirty worktrees)."""
    # Open intents indicate recovery needed
    if state.get("open_intents"):
        return True
    
    # Dirty worktrees indicate recovery needed
    for worktree in state.get("worktrees", []):
        if worktree.get("uncommitted_files") or worktree.get("staged_files"):
            return True
    
    return False


def print_summary(state: dict[str, Any]) -> None:
    """Print human-readable summary to stderr."""
    summary_lines = ["=== Session Recovery Summary ==="]
    
    # Open intents
    open_intents = state.get("open_intents", [])
    if open_intents:
        summary_lines.append(f"\nOpen Intents ({len(open_intents)}):")
        for intent in open_intents:
            summary_lines.append(
                f"  - {intent.get('story_id', '?')}: {intent.get('step', '?')} "
                f"(agent: {intent.get('agent', '?')})"
            )
    else:
        summary_lines.append("\nNo open intents.")
    
    # Worktrees
    worktrees = state.get("worktrees", [])
    if worktrees:
        summary_lines.append(f"\nWorktrees ({len(worktrees)}):")
        for wt in worktrees:
            uncommitted = len(wt.get("uncommitted_files", []))
            staged = len(wt.get("staged_files", []))
            branch = wt.get("branch", "?")
            path = wt.get("path", "?")
            
            status_parts = []
            if uncommitted:
                status_parts.append(f"{uncommitted} uncommitted")
            if staged:
                status_parts.append(f"{staged} staged")
            if wt.get("merge_conflicts"):
                status_parts.append("conflicts")
            if wt.get("detached_head"):
                status_parts.append("detached")
            
            status_str = ", ".join(status_parts) if status_parts else "clean"
            summary_lines.append(f"  - {path} ({branch}): {status_str}")
    else:
        summary_lines.append("\nNo worktrees.")
    
    # Main state
    main_state = state.get("main_state", {})
    ahead = main_state.get("ahead", 0)
    behind = main_state.get("behind", 0)
    dirty = main_state.get("dirty", False)
    
    main_status = []
    if ahead:
        main_status.append(f"{ahead} ahead")
    if behind:
        main_status.append(f"{behind} behind")
    if dirty:
        main_status.append("dirty")
    
    if main_status:
        summary_lines.append(f"\nMain branch: {', '.join(main_status)}")
    else:
        summary_lines.append("\nMain branch: clean")
    
    # QA state
    qa_state = state.get("qa_state", {})
    if qa_state:
        summary_lines.append(f"\nQA State ({len(qa_state)} stories):")
        for story_id, qa_info in sorted(qa_state.items()):
            verdict = qa_info.get("last_verdict", "?")
            summary_lines.append(f"  - {story_id}: {verdict}")
    
    # Feature claims
    claims = state.get("feature_claims", [])
    if claims:
        summary_lines.append(f"\nFeature Claims ({len(claims)}):")
        for claim in claims:
            summary_lines.append(
                f"  - {claim.get('feature', '?')}: {claim.get('owner', '?')} "
                f"({claim.get('status', '?')})"
            )
    
    print("\n".join(summary_lines), file=sys.stderr)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Collect pipeline state for session recovery"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 if clean, 1 if recovery items exist",
    )
    
    args = parser.parse_args()
    
    # Use current directory as repo root
    repo_path = Path.cwd()
    
    # Pull latest changes before scanning state
    pull_code, pull_out, pull_err = run_git_command(["pull"], repo_path)
    pull_output = (pull_out + "\n" + pull_err).strip()
    if pull_output:
        print(pull_output, file=sys.stderr)
    if pull_code != 0:
        print("Warning: git pull failed (continuing with local state)", file=sys.stderr)
    
    # Collect state
    state = collect_state(repo_path)
    
    # Output JSON to stdout
    print(json.dumps(state, indent=2))
    
    # Print summary to stderr
    print_summary(state)
    
    # Handle --check flag
    if args.check:
        if has_recovery_items(state):
            return 1
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
