"""
Local folder ingester.

Reads a local repository path, selects the most informative files,
reads their content, and produces a structured RepoSummary.

No LLM calls here — this is pure file I/O.
The RepoSummary is passed to the Concept Extractor agent.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from repo_analysis.file_scorer import walk_and_score, select_files
from repo_analysis.framework_detector import detect_frameworks, DetectedFramework


@dataclass
class FileContent:
    relative_path: str
    extension: str
    size_bytes: int
    content: str
    truncated: bool = False


@dataclass
class RepoSummary:
    repo_name: str
    input_type: str                          # "local" | "github"
    total_files: int
    total_dirs: int
    selected_files: list[FileContent]
    frameworks: list[DetectedFramework]
    directory_tree: str                      # abbreviated tree view
    skipped_dirs: list[str]
    error: Optional[str] = None


MAX_FILE_CHARS = 8_000   # max chars to read per file
MAX_TOTAL_FILES = 20     # max files to select
MAX_TOTAL_CHARS = 80_000 # total char budget across all files


def ingest_local_repo(repo_path: str) -> RepoSummary:
    """
    Main entry point for local repo ingestion.
    Takes a local folder path string and returns a RepoSummary.
    """
    root = Path(repo_path).expanduser().resolve()

    if not root.exists():
        return RepoSummary(
            repo_name=root.name,
            input_type="local",
            total_files=0,
            total_dirs=0,
            selected_files=[],
            frameworks=[],
            directory_tree="",
            skipped_dirs=[],
            error=f"Path does not exist: {root}",
        )

    if not root.is_dir():
        return RepoSummary(
            repo_name=root.name,
            input_type="local",
            total_files=0,
            total_dirs=0,
            selected_files=[],
            frameworks=[],
            directory_tree="",
            skipped_dirs=[],
            error=f"Path is not a directory: {root}",
        )

    # Walk and score all files
    scored = walk_and_score(root)
    readable = [f for f in scored if not f.skip_reason]
    skipped = list({
        f.skip_reason.split(":")[1]
        for f in scored
        if f.skip_reason and ":" in f.skip_reason
    })

    total_files = len(readable)
    total_dirs = len([p for p in root.rglob("*") if p.is_dir()])

    # Select top files within budget
    selected_scored = select_files(readable, MAX_TOTAL_FILES, MAX_TOTAL_CHARS)

    # Read content of selected files
    file_contents = []
    for sf in selected_scored:
        try:
            raw = sf.path.read_text(encoding="utf-8", errors="ignore")
            truncated = len(raw) > MAX_FILE_CHARS
            content = raw[:MAX_FILE_CHARS] if truncated else raw
            file_contents.append(FileContent(
                relative_path=sf.relative_path,
                extension=sf.extension,
                size_bytes=sf.size_bytes,
                content=content,
                truncated=truncated,
            ))
        except Exception as e:
            file_contents.append(FileContent(
                relative_path=sf.relative_path,
                extension=sf.extension,
                size_bytes=sf.size_bytes,
                content=f"[could not read: {e}]",
            ))

    # Detect frameworks
    all_paths = [str(f.relative_path) for f in readable]
    frameworks = detect_frameworks(root, all_paths)

    # Build abbreviated directory tree
    tree = _build_tree(root, max_depth=3)

    return RepoSummary(
        repo_name=root.name,
        input_type="local",
        total_files=total_files,
        total_dirs=total_dirs,
        selected_files=file_contents,
        frameworks=frameworks,
        directory_tree=tree,
        skipped_dirs=skipped,
    )


def _build_tree(root: Path, max_depth: int = 3) -> str:
    """Build an abbreviated directory tree string."""
    lines = [root.name + "/"]

    def _walk(path: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return

        # Skip noise dirs
        from repo_analysis.file_scorer import SKIP_DIRS
        entries = [
            e for e in entries
            if not (e.is_dir() and e.name.lower() in SKIP_DIRS)
            and not e.name.startswith(".")
        ]

        for i, entry in enumerate(entries[:20]):  # max 20 entries per level
            is_last = i == len(entries[:20]) - 1
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + entry.name + ("/" if entry.is_dir() else ""))
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension, depth + 1)

        if len(list(path.iterdir())) > 20:
            lines.append(prefix + "    ... (truncated)")

    _walk(root, "", 1)
    return "\n".join(lines)
