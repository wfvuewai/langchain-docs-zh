"""Build Chinese documentation for GitHub Pages deployment.

Usage:
    python scripts/build_zh.py

This script:
1. Runs the standard pipeline to generate build/ with English + shared assets
2. Copies Chinese content from src/zh/ to build/zh/
3. Uses docs.zh.json as the main docs.json for building
"""

import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
BUILD_DIR = REPO_ROOT / "build"

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline_build() -> None:
    """Run the standard pipeline build to generate build/ directory."""
    logger.info("Step 1: Running standard pipeline build...")
    result = subprocess.run(
        [sys.executable, "-m", "pipeline", "build"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Pipeline build failed:\n%s", result.stderr)
        sys.exit(1)
    logger.info("Pipeline build complete.")


def copy_chinese_content() -> None:
    """Copy Chinese content from src/zh/ to build/zh/."""
    zh_src = SRC_DIR / "zh"
    zh_dst = BUILD_DIR / "zh"

    if not zh_src.exists():
        logger.warning("src/zh/ not found, skipping Chinese content copy")
        return

    logger.info("Step 2: Copying Chinese content to build/zh/...")

    if zh_dst.exists():
        shutil.rmtree(zh_dst)
    zh_dst.mkdir(parents=True, exist_ok=True)

    for item in zh_src.rglob("*"):
        if item.is_file() and item.suffix.lower() in {
            ".mdx", ".md", ".json", ".yml", ".yaml",
        }:
            rel_path = item.relative_to(zh_src)
            dest = zh_dst / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            logger.debug("  Copied: zh/%s", rel_path)

    logger.info("Chinese content copied.")


def remove_english_content() -> None:
    """Remove English-only content from build/ to speed up mint export."""
    logger.info("Step 3: Removing English-only content from build/...")

    dirs_to_remove = ["langsmith", "oss"]
    for dir_name in dirs_to_remove:
        dir_path = BUILD_DIR / dir_name
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(dir_path)
            logger.info("  Removed: %s/", dir_name)

    files_to_remove = ["index.mdx", "playground.mdx", "use-these-docs.mdx"]
    for file_name in files_to_remove:
        file_path = BUILD_DIR / file_name
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            logger.info("  Removed: %s", file_name)

    remaining = sum(1 for _ in BUILD_DIR.rglob("*") if _.is_file())
    logger.info("Files remaining in build/: %d", remaining)


def replace_docs_json() -> None:
    """Replace build/docs.json with docs.zh.json."""
    zh_config = SRC_DIR / "docs.zh.json"
    build_config = BUILD_DIR / "docs.json"

    if not zh_config.exists():
        logger.warning("docs.zh.json not found, skipping replacement")
        return

    logger.info("Step 4: Replacing docs.json with docs.zh.json...")
    shutil.copy2(zh_config, build_config)
    logger.info("docs.json replaced.")


def main() -> None:
    run_pipeline_build()
    copy_chinese_content()
    remove_english_content()
    replace_docs_json()
    logger.info("✅ Chinese build preparation complete.")


if __name__ == "__main__":
    main()