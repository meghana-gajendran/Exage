"""
Framework and technology detection.

Detects what technologies a repo uses based on:
- Config files present
- Dependencies declared
- File extensions and patterns
- Directory structure

This runs before any LLM call — it's pure file-system heuristics.
The output tells downstream agents what concept graph to use for gap detection.
"""

from pathlib import Path
from dataclasses import dataclass
import json
import re


@dataclass
class DetectedFramework:
    name: str
    confidence: str  # "high" | "medium" | "low"
    evidence: str    # what file/pattern triggered detection


def detect_frameworks(repo_root: Path, file_paths: list[str]) -> list[DetectedFramework]:
    """Detect frameworks and technologies from file presence and content."""
    detected = []
    path_set = set(file_paths)

    def has_file(name: str) -> bool:
        return any(name in p for p in path_set)

    def has_ext(ext: str) -> bool:
        return any(p.endswith(ext) for p in path_set)

    # --- Data / Analytics ---
    if has_file("dbt_project.yml"):
        detected.append(DetectedFramework("dbt", "high", "dbt_project.yml present"))
    if has_file("airflow") or has_file("dag") or has_file("DAG"):
        detected.append(DetectedFramework("Apache Airflow", "medium", "DAG files detected"))
    if has_file("spark") or has_file("pyspark"):
        detected.append(DetectedFramework("Apache Spark", "medium", "Spark references detected"))

    # --- Python ecosystem ---
    if has_file("requirements.txt") or has_file("pyproject.toml") or has_file("setup.py"):
        detected.append(DetectedFramework("Python", "high", "Python project files present"))

        # Read requirements for specific frameworks
        req_file = repo_root / "requirements.txt"
        pyproject = repo_root / "pyproject.toml"

        deps_text = ""
        if req_file.exists():
            try:
                deps_text = req_file.read_text(encoding="utf-8", errors="ignore").lower()
            except Exception:
                pass
        if pyproject.exists():
            try:
                deps_text += pyproject.read_text(encoding="utf-8", errors="ignore").lower()
            except Exception:
                pass

        if "fastapi" in deps_text:
            detected.append(DetectedFramework("FastAPI", "high", "fastapi in dependencies"))
        if "django" in deps_text:
            detected.append(DetectedFramework("Django", "high", "django in dependencies"))
        if "flask" in deps_text:
            detected.append(DetectedFramework("Flask", "high", "flask in dependencies"))
        if "langchain" in deps_text:
            detected.append(DetectedFramework("LangChain", "high", "langchain in dependencies"))
        if "openai" in deps_text:
            detected.append(DetectedFramework("OpenAI API", "high", "openai in dependencies"))
        if "sqlalchemy" in deps_text:
            detected.append(DetectedFramework("SQLAlchemy", "high", "sqlalchemy in dependencies"))
        if "pytest" in deps_text:
            detected.append(DetectedFramework("pytest", "high", "pytest in dependencies"))
        if "pandas" in deps_text:
            detected.append(DetectedFramework("pandas", "high", "pandas in dependencies"))

    # --- JavaScript / TypeScript ecosystem ---
    if has_file("package.json"):
        detected.append(DetectedFramework("Node.js", "high", "package.json present"))

        pkg_file = repo_root / "package.json"
        pkg_text = ""
        if pkg_file.exists():
            try:
                pkg = json.loads(pkg_file.read_text(encoding="utf-8", errors="ignore"))
                all_deps = {
                    **pkg.get("dependencies", {}),
                    **pkg.get("devDependencies", {}),
                }
                pkg_text = " ".join(all_deps.keys()).lower()
            except Exception:
                pkg_text = pkg_file.read_text(encoding="utf-8", errors="ignore").lower()

        if "next" in pkg_text:
            detected.append(DetectedFramework("Next.js", "high", "next in package.json"))
        if "react" in pkg_text:
            detected.append(DetectedFramework("React", "high", "react in package.json"))
        if "vue" in pkg_text:
            detected.append(DetectedFramework("Vue.js", "high", "vue in package.json"))
        if "express" in pkg_text:
            detected.append(DetectedFramework("Express", "high", "express in package.json"))
        if "typescript" in pkg_text or has_ext(".ts"):
            detected.append(DetectedFramework("TypeScript", "high", "TypeScript files or dependency"))
        if "tailwind" in pkg_text:
            detected.append(DetectedFramework("Tailwind CSS", "high", "tailwindcss in package.json"))
        if "prisma" in pkg_text or has_file("schema.prisma"):
            detected.append(DetectedFramework("Prisma", "high", "Prisma detected"))

    # --- Infrastructure / DevOps ---
    if has_file("Dockerfile"):
        detected.append(DetectedFramework("Docker", "high", "Dockerfile present"))
    if has_file("docker-compose"):
        detected.append(DetectedFramework("Docker Compose", "high", "docker-compose file present"))
    if has_file("kubernetes") or has_file(".yaml") and any("kind:" in p for p in path_set):
        detected.append(DetectedFramework("Kubernetes", "medium", "Kubernetes manifests detected"))
    if has_file(".github/workflows"):
        detected.append(DetectedFramework("GitHub Actions", "high", "workflow files present"))
    if has_file("terraform") or has_ext(".tf"):
        detected.append(DetectedFramework("Terraform", "high", "Terraform files detected"))

    # --- Databases ---
    if has_ext(".sql"):
        detected.append(DetectedFramework("SQL", "high", "SQL files present"))
    if has_file("prisma") or has_file("schema.prisma"):
        detected.append(DetectedFramework("Prisma ORM", "high", "Prisma schema present"))
    if has_file("alembic.ini") or has_file("alembic"):
        detected.append(DetectedFramework("Alembic", "high", "Alembic migrations detected"))

    # --- Other languages ---
    if has_file("Cargo.toml"):
        detected.append(DetectedFramework("Rust", "high", "Cargo.toml present"))
    if has_file("go.mod"):
        detected.append(DetectedFramework("Go", "high", "go.mod present"))
    if has_file("pom.xml") or has_file("build.gradle"):
        detected.append(DetectedFramework("Java/JVM", "high", "Java build files present"))

    # Deduplicate
    seen = set()
    unique = []
    for f in detected:
        if f.name not in seen:
            seen.add(f.name)
            unique.append(f)

    return unique
