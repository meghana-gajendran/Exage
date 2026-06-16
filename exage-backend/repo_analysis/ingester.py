"""
Repo Ingester — main entry point.

Routes to the correct ingester based on input type:
- GitHub URL → github_ingester
- Local path → local_ingester

Returns a RepoSummary in both cases — same structure,
so downstream agents don't need to know where the repo came from.
"""

from typing import Optional
from repo_analysis.ingesters.local_ingester import RepoSummary, ingest_local_repo
from repo_analysis.ingesters.github_ingester import ingest_github_repo


def is_github_url(input_str: str) -> bool:
    return input_str.strip().startswith("https://github.com/") or \
           input_str.strip().startswith("http://github.com/")


def ingest_repo(
    repo_input: str,
    github_token: Optional[str] = None,
) -> RepoSummary:
    """
    Main entry point. Takes either a local path or a GitHub URL.
    Returns a RepoSummary ready for the Concept Extractor agent.
    """
    if is_github_url(repo_input):
        return ingest_github_repo(repo_input, github_token)
    else:
        return ingest_local_repo(repo_input)


def format_summary_for_llm(summary: RepoSummary) -> str:
    """
    Formats a RepoSummary into a clean string for LLM consumption.
    This is what gets passed to the Concept Extractor as context.
    """
    lines = []

    lines.append(f"Repository: {summary.repo_name}")
    lines.append(f"Source: {summary.input_type}")
    lines.append(f"Total files: {summary.total_files}")
    lines.append("")

    if summary.frameworks:
        lines.append("Detected technologies:")
        for fw in summary.frameworks:
            lines.append(f"  - {fw.name} ({fw.confidence} confidence) — {fw.evidence}")
        lines.append("")

    lines.append("Directory structure:")
    lines.append(summary.directory_tree)
    lines.append("")

    lines.append(f"Selected files for analysis ({len(summary.selected_files)} files):")
    lines.append("")

    for fc in summary.selected_files:
        trunc_note = " [truncated]" if fc.truncated else ""
        lines.append(f"{'='*60}")
        lines.append(f"FILE: {fc.relative_path}{trunc_note}")
        lines.append(f"{'='*60}")
        lines.append(fc.content)
        lines.append("")

    return "\n".join(lines)
