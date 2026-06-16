"""
File scoring logic for the repo ingester.

The ingester can't read every file — large repos can have thousands.
This module scores each file by how informative it's likely to be,
so we can select the best N files within a token budget.

Scoring is based on:
- File type (config files > source files > docs > everything else)
- Location (root-level and core directories > deeply nested)
- Size (too small = probably empty, too large = probably generated)
- Name signals (main, index, core, base > utils, helpers, migrations)
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# Directories to skip entirely — noise, not signal
SKIP_DIRS = {
    "node_modules", "venv", ".venv", "env", ".env",
    "__pycache__", ".git", ".github", ".next", "dist",
    "build", "out", "target", "coverage", ".pytest_cache",
    ".mypy_cache", "htmlcov", "eggs", ".eggs", "site-packages",
    "vendor", "bower_components", ".tox", "migrations",
}

# File extensions to skip — binary, generated, lock files
SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib",
    ".exe", ".bin", ".lock", ".sum", ".png", ".jpg",
    ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".mp3", ".wav", ".zip",
    ".tar", ".gz", ".db", ".sqlite", ".sqlite3",
    ".min.js", ".min.css", ".map",
}

# High-value config and entry point files — always include if present
HIGH_VALUE_NAMES = {
    "dbt_project.yml", "profiles.yml", "packages.yml",
    "package.json", "pyproject.toml", "setup.py", "setup.cfg",
    "requirements.txt", "Pipfile", "Cargo.toml", "go.mod",
    "docker-compose.yml", "Dockerfile", "docker-compose.yaml",
    "main.py", "app.py", "index.js", "index.ts", "server.py",
    "server.ts", "manage.py", "wsgi.py", "asgi.py",
    "README.md", "README.rst", "schema.prisma",
    "next.config.js", "next.config.ts", "vite.config.ts",
    "webpack.config.js", ".env.example",
}

# Extension scores — higher = more informative
EXTENSION_SCORES = {
    ".py": 8, ".ts": 8, ".tsx": 7, ".js": 7, ".jsx": 6,
    ".sql": 9, ".yml": 7, ".yaml": 7, ".toml": 7,
    ".go": 8, ".rs": 8, ".java": 7, ".kt": 7,
    ".rb": 7, ".php": 6, ".cs": 7, ".cpp": 7, ".c": 6,
    ".sh": 5, ".bash": 5, ".md": 4, ".txt": 3,
    ".json": 5, ".xml": 4, ".html": 4, ".css": 3,
}

# Directory name scores — signals of importance
DIR_SCORES = {
    "models": 9, "src": 8, "app": 8, "core": 9, "lib": 7,
    "api": 8, "agents": 9, "services": 8, "controllers": 7,
    "macros": 8, "tests": 6, "test": 6, "specs": 6,
    "config": 7, "configs": 7, "schemas": 7,
    "components": 6, "pages": 6, "routes": 7,
    "utils": 4, "helpers": 4, "common": 4, "shared": 4,
    "static": 2, "assets": 2, "public": 2, "media": 1,
}

# Filename signals
HIGH_VALUE_STEMS = {
    "main", "app", "server", "index", "core", "base",
    "model", "agent", "pipeline", "runner", "config",
    "schema", "router", "handler", "controller",
}

LOW_VALUE_STEMS = {
    "migration", "seed", "fixture", "mock", "stub",
    "generated", "auto", "legacy", "deprecated", "old",
}


@dataclass
class ScoredFile:
    path: Path
    relative_path: str
    extension: str
    size_bytes: int
    score: float
    is_high_value: bool = False
    skip_reason: Optional[str] = None


def should_skip_path(path: Path) -> Optional[str]:
    """Return a skip reason if the file should be excluded, else None."""
    # Skip hidden files/dirs (except .env.example)
    if any(part.startswith(".") and part != ".env.example" for part in path.parts):
        return "hidden"

    # Skip known noisy directories
    for part in path.parts:
        if part.lower() in SKIP_DIRS:
            return f"skip_dir:{part}"

    # Skip by extension
    suffix = path.suffix.lower()
    # Handle .min.js, .min.css
    name_lower = path.name.lower()
    if ".min." in name_lower:
        return "minified"
    if suffix in SKIP_EXTENSIONS:
        return f"skip_ext:{suffix}"

    return None


def score_file(path: Path, repo_root: Path) -> ScoredFile:
    """Score a file by informativeness. Higher = more worth reading."""
    relative = path.relative_to(repo_root)
    rel_str = str(relative)
    ext = path.suffix.lower()
    size = path.stat().st_size if path.exists() else 0

    score = 0.0
    is_high_value = False

    # High-value filenames always get a boost
    if path.name in HIGH_VALUE_NAMES:
        score += 20
        is_high_value = True

    # Extension score
    score += EXTENSION_SCORES.get(ext, 2)

    # Directory score — use the highest-scoring parent directory
    for part in relative.parts[:-1]:
        dir_score = DIR_SCORES.get(part.lower(), 0)
        score += dir_score * 0.5  # diminishing weight per level

    # Stem signals
    stem_lower = path.stem.lower()
    if stem_lower in HIGH_VALUE_STEMS:
        score += 3
    if stem_lower in LOW_VALUE_STEMS:
        score -= 5

    # Depth penalty — deeply nested files are less likely to be core
    depth = len(relative.parts) - 1
    score -= depth * 0.5

    # Size filter — too small or too large = less useful
    if size < 50:
        score -= 5  # probably empty
    elif size > 100_000:
        score -= 10  # probably generated or too large to read fully
    elif 200 < size < 20_000:
        score += 2  # ideal size range

    return ScoredFile(
        path=path,
        relative_path=rel_str,
        extension=ext,
        size_bytes=size,
        score=score,
        is_high_value=is_high_value,
    )


def walk_and_score(repo_root: Path) -> list[ScoredFile]:
    """Walk the repo, skip noise, score every remaining file."""
    scored = []

    for file_path in repo_root.rglob("*"):
        if not file_path.is_file():
            continue

        relative = file_path.relative_to(repo_root)
        skip_reason = should_skip_path(relative)

        if skip_reason:
            scored.append(ScoredFile(
                path=file_path,
                relative_path=str(relative),
                extension=file_path.suffix.lower(),
                size_bytes=0,
                score=-999,
                skip_reason=skip_reason,
            ))
            continue

        scored.append(score_file(file_path, repo_root))

    return sorted(scored, key=lambda f: f.score, reverse=True)


def select_files(
    scored_files: list[ScoredFile],
    max_files: int = 20,
    max_total_chars: int = 80_000,
) -> list[ScoredFile]:
    """
    Select the top N files within a character budget.
    Always include high-value files first, then fill with the rest.
    """
    selected = []
    total_chars = 0

    # First pass: always include high-value files
    for f in scored_files:
        if f.skip_reason:
            continue
        if f.is_high_value and f.size_bytes > 0:
            selected.append(f)
            total_chars += f.size_bytes

    # Second pass: fill remaining slots by score
    for f in scored_files:
        if len(selected) >= max_files:
            break
        if f.skip_reason:
            continue
        if f in selected:
            continue
        if total_chars + f.size_bytes > max_total_chars:
            continue
        selected.append(f)
        total_chars += f.size_bytes

    return selected
