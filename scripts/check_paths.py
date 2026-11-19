"""Validate that file paths referenced in tracked Markdown actually exist.

Guards against stale / hallucinated references drifting into the docs. Scans
every tracked ``*.md`` file, pulls out Markdown-link targets and inline-code
tokens that look like repo paths, and fails if any point at a file that is
neither present on disk nor an expected (git-ignored) runtime artifact.

Exit codes: 0 = all references resolve, 1 = one or more dangling references,
2 = not a git repo / git unavailable.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Fenced code blocks (``` ... ```) hold ASCII trees and diagrams, not real
# references, so we strip them before scanning.
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
INLINE_RE = re.compile(r"`([^`]+)`")

# A token is treated as a path only when it contains a path separator or ends
# with one of these extensions (keeps prose like `MAX_MESSAGES = 500` or
# `list[dict]` from being mistaken for a file).
PATH_EXTS = (
    ".py", ".md", ".html", ".csv", ".txt", ".json", ".sh", ".ps1",
    ".yml", ".yaml", ".toml", ".cfg", ".ini", ".env",
)

SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "tel:")
# Tokens with these never denote a repo file: usage strings (`{a|b}`), globs,
# whitespace-separated prose, or absolute/route paths (`/analyze`).
BAD_CHARS = set(" \t\n{}|<>*?\"")


def git_root() -> Path | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return Path(out.stdout.strip())


def tracked_markdown(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    return [root / line for line in out.stdout.splitlines() if line]


def looks_like_path(token: str) -> bool:
    if not token or token.startswith(SKIP_PREFIXES) or token.startswith("/"):
        return False
    if BAD_CHARS & set(token):
        return False
    if "/" in token:
        return True
    return token.lower().endswith(PATH_EXTS)


def candidates(text: str) -> list[str]:
    body = FENCE_RE.sub("", text)
    found = [t.split("#", 1)[0] for t in LINK_RE.findall(body)]
    found += [t.strip() for t in INLINE_RE.findall(body)]
    return [t for t in found if looks_like_path(t)]


def is_ignored(root: Path, path: Path) -> bool:
    """True for git-ignored paths (e.g. .env, scripts/.dev.pid) — expected absent."""
    rc = subprocess.run(
        ["git", "check-ignore", "-q", str(path)], cwd=root,
        stderr=subprocess.DEVNULL,
    ).returncode
    return rc == 0


def resolves(root: Path, md_dir: Path, ref: str) -> bool:
    """A reference is valid if it exists (or is an expected ignored artifact)
    relative to either the doc's own directory or the repo root."""
    for base in (md_dir, root):
        target = (base / ref).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            continue  # escapes the repo; not a repo path
        if target.exists() or is_ignored(root, target):
            return True
    return False


def main() -> int:
    root = git_root()
    if root is None:
        print("FAIL: not a git repository (or git not found)")
        return 2

    dangling: list[tuple[Path, str]] = []
    checked = 0
    for md in tracked_markdown(root):
        md_dir = md.parent
        text = md.read_text(encoding="utf-8", errors="replace")
        for ref in candidates(text):
            checked += 1
            if not resolves(root, md_dir, ref):
                dangling.append((md.relative_to(root), ref))

    print(f"checked {checked} reference(s) across tracked Markdown")
    if dangling:
        print(f"DANGLING: {len(dangling)} reference(s) point at missing files:")
        for src, ref in dangling:
            print(f"  [FAIL] {src} -> {ref}")
        return 1
    print("PATHS OK")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    sys.exit(main())
