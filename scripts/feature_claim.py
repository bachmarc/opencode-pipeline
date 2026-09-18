#!/usr/bin/env python3
"""Feature claim/release script for multi-user isolation (Story 06-09).

Deterministic feature claiming with atomic git pull-check-commit-push.
Prevents race conditions that an LLM cannot handle reliably.

Uses only stdlib (json, argparse, pathlib, datetime, subprocess, socket, os).

Exit codes:
  0 - success
  1 - already claimed by someone else
  2 - feature not found
  3 - push conflict (max retries exceeded)
"""

import argparse
import json
import os
import socket
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def get_user_host() -> str:
    """Get user@host from git config and hostname."""
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=True,
        )
        email = result.stdout.strip()
    except subprocess.CalledProcessError:
        email = os.environ.get("USER", "unknown")
    
    hostname = socket.gethostname()
    return f"{email}@{hostname}"


def get_feature_path(repo_dir: Path, feature_name: str) -> Path:
    """Get the path to a feature's feature.md file."""
    return repo_dir / "docs" / "features" / feature_name / "feature.md"


def feature_exists(repo_dir: Path, feature_name: str) -> bool:
    """Check if a feature exists."""
    return get_feature_path(repo_dir, feature_name).exists()


def read_feature_md(repo_dir: Path, feature_name: str) -> dict:
    """Read and parse a feature.md file.
    
    Returns a dict with 'frontmatter' (dict) and 'body' (str).
    """
    path = get_feature_path(repo_dir, feature_name)
    content = path.read_text(encoding="utf-8")
    
    lines = content.splitlines(keepends=True)
    
    # Parse frontmatter
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"Invalid frontmatter in {path}")
    
    try:
        end_idx = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError(f"Unterminated frontmatter in {path}")
    
    frontmatter_lines = lines[1:end_idx]
    body_lines = lines[end_idx + 1 :]
    
    # Parse frontmatter key-value pairs
    frontmatter = {}
    for line in frontmatter_lines:
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Remove quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        frontmatter[key] = value
    
    body = "".join(body_lines)
    
    return {"frontmatter": frontmatter, "body": body}


def write_feature_md(
    repo_dir: Path,
    feature_name: str,
    frontmatter: dict,
    body: str,
) -> None:
    """Write a feature.md file with updated frontmatter."""
    path = get_feature_path(repo_dir, feature_name)
    
    # Build frontmatter
    fm_lines = ["---"]
    for key in sorted(frontmatter.keys()):
        value = frontmatter[key]
        # Quote string values that contain special characters or are empty
        if isinstance(value, str) and (
            value == "" or " " in value or "@" in value or ":" in value
        ):
            value = f'"{value}"'
        fm_lines.append(f"{key}: {value}")
    fm_lines.append("---")
    
    content = "\n".join(fm_lines) + "\n" + body
    path.write_text(content, encoding="utf-8")


def git_pull(repo_dir: Path, local_only: bool = False) -> bool:
    """Run git pull --rebase. Returns True on success."""
    if local_only:
        return True
    
    try:
        subprocess.run(
            ["git", "pull", "--rebase"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def git_commit(repo_dir: Path, message: str) -> bool:
    """Run git commit. Returns True on success."""
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def git_push(repo_dir: Path, local_only: bool = False) -> bool:
    """Run git push. Returns True on success."""
    if local_only:
        return True
    
    try:
        subprocess.run(
            ["git", "push"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def git_create_branch(repo_dir: Path, branch_name: str, local_only: bool = False) -> bool:
    """Create a branch if it doesn't exist. Returns True on success."""
    try:
        # Check if branch exists
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            cwd=repo_dir,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            # Branch exists
            return True
        
        # Create branch
        subprocess.run(
            ["git", "branch", branch_name],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        
        if not local_only:
            # Push branch to remote
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=repo_dir,
                capture_output=True,
                check=False,
            )
        
        return True
    except subprocess.CalledProcessError:
        return False


def cmd_claim(args: argparse.Namespace) -> int:
    """Claim a feature.
    
    Exit codes:
      0 - success
      1 - already claimed by someone else
      2 - feature not found
      3 - push conflict (max retries)
    """
    repo_dir = Path(args.repo_dir)
    feature_name = args.feature_name
    local_only = args.local_only
    
    # Check if feature exists
    if not feature_exists(repo_dir, feature_name):
        output = {"error": f"Feature '{feature_name}' not found", "claimed": False}
        print(json.dumps(output))
        return 2
    
    user_host = get_user_host()
    max_retries = 3
    
    for attempt in range(max_retries):
        # Pull latest changes
        if not git_pull(repo_dir, local_only):
            output = {"error": "Failed to pull", "claimed": False}
            print(json.dumps(output))
            return 3
        
        # Read feature.md
        try:
            data = read_feature_md(repo_dir, feature_name)
        except ValueError as e:
            output = {"error": f"Failed to read feature: {e}", "claimed": False}
            print(json.dumps(output))
            return 2
        
        frontmatter = data["frontmatter"]
        body = data["body"]
        
        # Check if already claimed by someone else
        current_status = frontmatter.get("status", "planned")
        current_owner = frontmatter.get("owner", "")
        
        if current_status == "claimed" and current_owner:
            if current_owner != user_host:
                # Different user has claimed it
                output = {
                    "error": f"Already claimed by {current_owner}",
                    "claimed": False,
                    "feature": feature_name,
                    "current_owner": current_owner,
                }
                print(json.dumps(output))
                return 1
            else:
                # Same user is claiming again - this is an error (already claimed)
                output = {
                    "error": "Already claimed by you",
                    "claimed": False,
                    "feature": feature_name,
                    "current_owner": current_owner,
                }
                print(json.dumps(output))
                return 1
        
        # Update frontmatter
        frontmatter["status"] = "claimed"
        frontmatter["owner"] = user_host
        frontmatter["claimed_at"] = datetime.now(UTC).isoformat()
        
        # Write updated feature.md
        try:
            write_feature_md(repo_dir, feature_name, frontmatter, body)
        except ValueError as e:
            output = {"error": f"Failed to write feature: {e}", "claimed": False}
            print(json.dumps(output))
            return 2
        
        # Commit
        if not git_commit(repo_dir, f"claim: {feature_name} by {user_host}"):
            output = {"error": "Failed to commit", "claimed": False}
            print(json.dumps(output))
            return 3
        
        # Push
        if git_push(repo_dir, local_only):
            # Success
            output = {
                "claimed": True,
                "feature": feature_name,
                "owner": user_host,
            }
            print(json.dumps(output))
            
            # Create feature branch
            git_create_branch(repo_dir, f"feature/{feature_name}", local_only)
            
            return 0
        
        # Push failed, retry
        if attempt < max_retries - 1:
            # Reset to HEAD to undo commit
            subprocess.run(
                ["git", "reset", "--hard", "HEAD~1"],
                cwd=repo_dir,
                capture_output=True,
                check=False,
            )
    
    # Max retries exceeded
    output = {"error": "Push conflict (max retries exceeded)", "claimed": False}
    print(json.dumps(output))
    return 3


def cmd_release(args: argparse.Namespace) -> int:
    """Release a feature.
    
    Exit codes:
      0 - success
      2 - feature not found
      3 - push conflict
    """
    repo_dir = Path(args.repo_dir)
    feature_name = args.feature_name
    local_only = args.local_only
    
    # Check if feature exists
    if not feature_exists(repo_dir, feature_name):
        output = {"error": f"Feature '{feature_name}' not found", "released": False}
        print(json.dumps(output))
        return 2
    
    # Pull latest changes
    if not git_pull(repo_dir, local_only):
        output = {"error": "Failed to pull", "released": False}
        print(json.dumps(output))
        return 3
    
    # Read feature.md
    try:
        data = read_feature_md(repo_dir, feature_name)
    except ValueError as e:
        output = {"error": f"Failed to read feature: {e}", "released": False}
        print(json.dumps(output))
        return 2
    
    frontmatter = data["frontmatter"]
    body = data["body"]
    
    # Reset status to planned and clear owner
    frontmatter["status"] = "planned"
    frontmatter["owner"] = ""
    # Remove claimed_at if present
    frontmatter.pop("claimed_at", None)
    
    # Write updated feature.md
    try:
        write_feature_md(repo_dir, feature_name, frontmatter, body)
    except ValueError as e:
        output = {"error": f"Failed to write feature: {e}", "released": False}
        print(json.dumps(output))
        return 2
    
    # Commit
    if not git_commit(repo_dir, f"release: {feature_name}"):
        output = {"error": "Failed to commit", "released": False}
        print(json.dumps(output))
        return 3
    
    # Push
    if not git_push(repo_dir, local_only):
        output = {"error": "Failed to push", "released": False}
        print(json.dumps(output))
        return 3
    
    output = {
        "released": True,
        "feature": feature_name,
    }
    print(json.dumps(output))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """List all features with claim state.
    
    Exit codes:
      0 - success
    """
    repo_dir = Path(args.repo_dir)
    
    features_dir = repo_dir / "docs" / "features"
    if not features_dir.exists():
        print(json.dumps([]))
        return 0
    
    features = []
    for feature_dir in sorted(features_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        
        feature_md = feature_dir / "feature.md"
        if not feature_md.exists():
            continue
        
        try:
            data = read_feature_md(repo_dir, feature_dir.name)
            frontmatter = data["frontmatter"]
            
            features.append({
                "feature": feature_dir.name,
                "id": frontmatter.get("id", ""),
                "title": frontmatter.get("title", ""),
                "status": frontmatter.get("status", "planned"),
                "owner": frontmatter.get("owner", ""),
                "claimed_at": frontmatter.get("claimed_at", ""),
            })
        except ValueError:
            # Skip features that can't be parsed
            pass
    
    print(json.dumps(features, indent=2))
    return 0


def cmd_check_stale(args: argparse.Namespace) -> int:
    """Find claims older than threshold.
    
    Exit codes:
      0 - success
    """
    repo_dir = Path(args.repo_dir)
    hours = args.hours
    
    features_dir = repo_dir / "docs" / "features"
    if not features_dir.exists():
        print(json.dumps([]))
        return 0
    
    now = datetime.now(UTC)
    stale_features = []
    
    for feature_dir in sorted(features_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        
        feature_md = feature_dir / "feature.md"
        if not feature_md.exists():
            continue
        
        try:
            data = read_feature_md(repo_dir, feature_dir.name)
            frontmatter = data["frontmatter"]
            
            status = frontmatter.get("status", "planned")
            claimed_at_str = frontmatter.get("claimed_at", "")
            
            if status == "claimed" and claimed_at_str:
                claimed_at = datetime.fromisoformat(claimed_at_str)
                age_hours = (now - claimed_at).total_seconds() / 3600
                
                if age_hours > hours:
                    stale_features.append({
                        "feature": feature_dir.name,
                        "id": frontmatter.get("id", ""),
                        "owner": frontmatter.get("owner", ""),
                        "claimed_at": claimed_at_str,
                        "age_hours": round(age_hours, 1),
                    })
        except ValueError:
            # Skip features that can't be parsed
            pass
    
    print(json.dumps(stale_features, indent=2))
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Feature claim/release script for multi-user isolation"
    )
    
    parser.add_argument(
        "--repo-dir",
        type=str,
        default=".",
        help="Repository directory (default: current directory)",
    )
    
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Skip git push/pull operations (for testing)",
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # claim subcommand
    claim_parser = subparsers.add_parser("claim", help="Claim a feature")
    claim_parser.add_argument("feature_name", help="Feature name")
    claim_parser.set_defaults(func=cmd_claim)
    
    # release subcommand
    release_parser = subparsers.add_parser("release", help="Release a feature")
    release_parser.add_argument("feature_name", help="Feature name")
    release_parser.set_defaults(func=cmd_release)
    
    # status subcommand
    status_parser = subparsers.add_parser("status", help="List all features")
    status_parser.set_defaults(func=cmd_status)
    
    # check-stale subcommand
    stale_parser = subparsers.add_parser("check-stale", help="Find stale claims")
    stale_parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Threshold in hours (default: 24)",
    )
    stale_parser.set_defaults(func=cmd_check_stale)
    
    args = parser.parse_args()
    
    try:
        return args.func(args)
    except (ValueError, OSError) as e:
        output = {"error": str(e)}
        print(json.dumps(output))
        return 1


if __name__ == "__main__":
    sys.exit(main())
