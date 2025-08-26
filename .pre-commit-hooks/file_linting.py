#!/usr/bin/env python3
# =============================================================================
# 🧪 File Linting Script
# - Ensures Python files have blank lines before and after `yield`
# - Automatically fixes missing blank lines
# - Modular, testable, CI/CD friendly
# =============================================================================

from pathlib import Path
import sys
from typing import List

from kraken_core import PathsConfig, custom_logger


# =============================================================================
# ⚙️ Helper Functions
# =============================================================================
def lint_and_fix_yield_spacing(file_path: Path) -> List[str]:
    """
    Check and automatically fix spacing around 'yield' in a single file.

    Args:
        file_path (Path): Path to the Python file.

    Returns:
        List[str]: List of violation messages (before fix).
    """
    violations: List[str] = []

    with file_path.open("r") as f:
        lines = f.read().splitlines()

    new_lines: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "yield " in line and file_path.name != "file_linting.py":
            # Check blank line before
            if i == 0 or lines[i - 1].strip() != "":
                violations.append(
                    f"{file_path}:{i+1}: Missing blank line before 'yield'"
                )
                new_lines.append("")  # insert blank line before

            new_lines.append(line)

            # Check blank line after
            if i == len(lines) - 1 or lines[i + 1].strip() != "":
                violations.append(
                    f"{file_path}:{i+1}: Missing blank line after 'yield'"
                )
                new_lines.append("")  # insert blank line after
            i += 1
        else:
            new_lines.append(line)
            i += 1

    # Only rewrite file if changes were made
    if violations:
        with file_path.open("w") as f:
            f.write("\n".join(new_lines) + "\n")

    if violations:
        custom_logger.info(f"Violations fixed in {file_path}: {violations}")
    return violations


def lint_files(files_to_check: List[Path]) -> int:
    """
    Run lint checks (and fix) on a list of files.

    Args:
        files_to_check (List[Path]): List of files to check.

    Returns:
        int: Exit code (0 = success, 1 = violations or missing files).
    """
    exit_code = 0

    for file_path in files_to_check:
        if not file_path.exists():
            custom_logger.error(f"File does not exist: {file_path}")
            exit_code = 1
            continue

        violations = lint_and_fix_yield_spacing(file_path)
        if violations:
            for v in violations:
                custom_logger.warning(v)
            exit_code = 1

    return exit_code


# =============================================================================
# 🏁 Main / Entry Point
# =============================================================================
def main() -> None:
    """
    CLI entry point for the file linting script.
    """
    try:
        files_to_check = list(PathsConfig.REPO_ROOT.rglob("*.py"))
        exit_code = lint_files(files_to_check)
        sys.exit(exit_code)
    except Exception as e:
        custom_logger.exception(f"Unexpected error in file_linting.py: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
