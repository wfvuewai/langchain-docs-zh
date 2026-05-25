#!/usr/bin/env python3
"""Helper script to track English file changes that need translation.

This script compares the current English source files against their Chinese
counterparts and reports:
1. English files that have no corresponding Chinese translation
2. English files that have been modified since the last sync

Usage:
    # Show pending translations (English files without Chinese versions)
    python scripts/sync_tracker.py --pending

    # Show recently changed English files (needs ref commit for comparison)
    python scripts/sync_tracker.py --diff --ref upstream/main
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
ZH_DIR = SRC_DIR / "zh"

# Directories that contain translatable content
CONTENT_DIRS = {
    "langsmith",
    "oss/concepts",
    "oss/contributing",
    "oss/deepagents",
    "oss/integrations",
    "oss/langchain",
    "oss/langgraph",
    "oss/python",
    "oss/javascript",
    "oss/reference",
}


def find_mdx_files(base_dir: Path) -> list[Path]:
    """Find all .mdx files in content directories under base_dir."""
    files = []
    for content_dir in CONTENT_DIRS:
        full_path = base_dir / content_dir
        if full_path.exists():
            for f in sorted(full_path.rglob("*.mdx")):
                files.append(f)
    # Also include index.mdx and other root mdx files
    for f in sorted(base_dir.glob("*.mdx")):
        files.append(f)
    return files


def show_pending() -> None:
    """Show English files that have no Chinese translation yet."""
    english_files = find_mdx_files(SRC_DIR)
    pending = []

    for eng_file in english_files:
        # Calculate the relative path from src/
        rel_path = eng_file.relative_to(SRC_DIR)
        # Map to src/zh/ path
        zh_path = ZH_DIR / rel_path

        if not zh_path.exists():
            pending.append(rel_path)

    if pending:
        print(f"📋 Files needing translation ({len(pending)}):\n")
        for f in pending:
            print(f"  src/{f}")
    else:
        print("✅ All English files have Chinese counterparts!")
        print("   (Check for updated content with --diff)")


def show_diff(ref: str = "upstream/main") -> None:
    """Show English files changed since ref commit."""
    result = subprocess.run(
        ["git", "diff", "--name-only", ref, "--", "src/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error running git diff: {result.stderr}")
        sys.exit(1)

    changed = [line for line in result.stdout.strip().split("\n") if line]

    if not changed:
        print("✅ No English files have changed since last sync.")
        return

    print(f"📝 Files changed since {ref} ({len(changed)}):\n")
    for f in changed:
        # Check if Chinese version exists
        zh_file = Path(str(f).replace("src/", "src/zh/", 1))
        status = "✅" if zh_file.exists() else "❌ needs translation"
        print(f"  {status} {f}")

    print(f"\nTo sync: git merge {ref}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Track English-to-Chinese sync status")
    parser.add_argument(
        "--pending",
        action="store_true",
        help="Show English files without Chinese translation",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show English files changed since --ref",
    )
    parser.add_argument(
        "--ref",
        default="upstream/main",
        help="Git ref to compare against (default: upstream/main)",
    )

    args = parser.parse_args()

    if not args.pending and not args.diff:
        parser.print_help()
        return

    if args.pending:
        show_pending()

    if args.diff:
        if args.pending:
            print()
        show_diff(args.ref)


if __name__ == "__main__":
    main()