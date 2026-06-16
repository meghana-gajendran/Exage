"""
GitHub URL ingester.

Fetches a public GitHub repository using the GitHub API.
No cloning needed — we use the Contents API to fetch the file tree
and download only the files we decide are worth reading.

Rate limits: GitHub API allows 60 requests/hour unauthenticated,
or 5000/hour with a token. For MVP, unauthenticated is fine for small repos.

Supported URL formats:
- https://github.com/owner/repo
- https://github.com/owner/repo.git
- https://github.com/owner/repo/tree/branch
"""

import re
import urllib.request
import urllib.error
import json
import base64
from dataclasses import dataclass
from typing import Optional
from repo_analysis.file_scorer import (
    should_skip_path, score_file, SKIP_DIRS, SKIP_EXTENSIONS,
    HIGH_VALUE_NAMES, EXTENSION_SCORES
)
from repo_analysis.framework_detector import detect_frameworks
from repo_analysis.ingesters.local_ingester import (
    RepoSummary, FileContent, MAX_FILE_CHARS, MAX_TOTAL_FILES
)
from pathlib import Path, PurePosixPath


GITHUB_API = "https://api.github.com"
MAX_TREE_FILES = 500  # don't process more than this many files from the tree


def parse_github_url(url: str) -> tuple[str, str, str]:
    """
    Parse a GitHub URL into (owner, repo, branch).
    Returns branch as empty string if not specified.
    """
    url = url.strip().rstrip("/").removesuffix(".git")

    # https://github.com/owner/repo/tree/branchname
    match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?",
        url
    )
    if not match:
        raise ValueError(f"Could not parse GitHub URL: {url}")

    owner = match.group(1)
    repo = match.group(2)
    branch = match.group(3) or ""
    return owner, repo, branch


def _github_get(url: str, token: Optional[str] = None) -> dict | list:
    """Make a GitHub API GET request and return parsed JSON."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "ExAge-RepoIngester/1.0")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API error {e.code}: {e.reason} for {url}")


def _score_github_file(path_str: str, size: int) -> float:
    """Score a GitHub file path by informativeness (no filesystem access)."""
    p = PurePosixPath(path_str)
    score = 0.0

    # Skip checks
    ext = p.suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return -999
    if any(part.lower() in SKIP_DIRS for part in p.parts):
        return -999
    if p.name in HIGH_VALUE_NAMES:
        score += 20

    score += EXTENSION_SCORES.get(ext, 2)

    # Depth penalty
    depth = len(p.parts) - 1
    score -= depth * 0.5

    # Size filter
    if size < 50:
        score -= 5
    elif size > 100_000:
        score -= 10
    elif 200 < size < 20_000:
        score += 2

    return score


def ingest_github_repo(
    github_url: str,
    github_token: Optional[str] = None,
) -> RepoSummary:
    """
    Main entry point for GitHub repo ingestion.
    Fetches repo structure and selected file contents via GitHub API.
    """
    try:
        owner, repo, branch = parse_github_url(github_url)
    except ValueError as e:
        return RepoSummary(
            repo_name="unknown",
            input_type="github",
            total_files=0, total_dirs=0,
            selected_files=[], frameworks=[],
            directory_tree="", skipped_dirs=[],
            error=str(e),
        )

    # Get default branch if not specified
    if not branch:
        try:
            repo_info = _github_get(f"{GITHUB_API}/repos/{owner}/{repo}", github_token)
            branch = repo_info.get("default_branch", "main")
        except Exception as e:
            return RepoSummary(
                repo_name=repo,
                input_type="github",
                total_files=0, total_dirs=0,
                selected_files=[], frameworks=[],
                directory_tree="", skipped_dirs=[],
                error=f"Could not fetch repo info: {e}",
            )

    # Fetch git tree recursively
    try:
        tree_data = _github_get(
            f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
            github_token,
        )
    except Exception as e:
        return RepoSummary(
            repo_name=repo,
            input_type="github",
            total_files=0, total_dirs=0,
            selected_files=[], frameworks=[],
            directory_tree="", skipped_dirs=[],
            error=f"Could not fetch repo tree: {e}",
        )

    tree_items = tree_data.get("tree", [])
    files = [item for item in tree_items if item.get("type") == "blob"]
    dirs = [item for item in tree_items if item.get("type") == "tree"]

    # Score and select files
    scored = []
    for f in files[:MAX_TREE_FILES]:
        path_str = f.get("path", "")
        size = f.get("size", 0)
        score = _score_github_file(path_str, size)
        if score > -999:
            scored.append((score, path_str, size))

    scored.sort(reverse=True)
    selected = scored[:MAX_TOTAL_FILES]

    # Fetch content of selected files
    file_contents = []
    all_paths = [path for _, path, _ in scored]

    for _, path_str, size in selected:
        try:
            content_data = _github_get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path_str}?ref={branch}",
                github_token,
            )
            raw_content = base64.b64decode(content_data.get("content", "")).decode("utf-8", errors="ignore")
            truncated = len(raw_content) > MAX_FILE_CHARS
            content = raw_content[:MAX_FILE_CHARS] if truncated else raw_content

            file_contents.append(FileContent(
                relative_path=path_str,
                extension=PurePosixPath(path_str).suffix.lower(),
                size_bytes=size,
                content=content,
                truncated=truncated,
            ))
        except Exception as e:
            file_contents.append(FileContent(
                relative_path=path_str,
                extension=PurePosixPath(path_str).suffix.lower(),
                size_bytes=size,
                content=f"[could not fetch: {e}]",
            ))

    # Detect frameworks from path list
    frameworks = detect_frameworks(Path("/"), all_paths)

    # Build simple tree from dir list
    tree_lines = [f"{owner}/{repo}/"]
    top_dirs = sorted({p.split("/")[0] for p in all_paths if "/" in p})[:20]
    for d in top_dirs:
        tree_lines.append(f"├── {d}/")
    tree_str = "\n".join(tree_lines)

    return RepoSummary(
        repo_name=repo,
        input_type="github",
        total_files=len(files),
        total_dirs=len(dirs),
        selected_files=file_contents,
        frameworks=frameworks,
        directory_tree=tree_str,
        skipped_dirs=[],
    )
