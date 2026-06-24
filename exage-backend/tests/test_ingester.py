"""
Tests for Phase 1 — Repo Ingester.

These tests use a synthetic mini-repo created in a temp directory.
No real GitHub calls are made.
"""

import pytest
from pathlib import Path
from repo_analysis.file_scorer import walk_and_score, select_files, should_skip_path
from repo_analysis.framework_detector import detect_frameworks
from repo_analysis.ingesters.local_ingester import ingest_local_repo
from repo_analysis.ingester import ingest_repo, is_github_url, format_summary_for_llm


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mini_dbt_repo(tmp_path):
    """Creates a minimal dbt-like repo structure for testing."""
    (tmp_path / "dbt_project.yml").write_text("""
name: my_project
version: '1.0.0'
config-version: 2
model-paths: ["models"]
""")
    (tmp_path / "packages.yml").write_text("""
packages:
  - package: dbt-labs/dbt_utils
    version: 1.0.0
""")
    models = tmp_path / "models" / "staging"
    models.mkdir(parents=True)
    (models / "stg_orders.sql").write_text("""
with source as (
    select * from {{ source('raw', 'orders') }}
),
renamed as (
    select
        id as order_id,
        user_id,
        status,
        created_at
    from source
)
select * from renamed
""")

    macros = tmp_path / "macros"
    macros.mkdir()
    (macros / "generate_surrogate_key.sql").write_text("""
{% macro generate_surrogate_key(field_list) %}
    {{ dbt_utils.generate_surrogate_key(field_list) }}
{% endmacro %}
""")

    # Add some noise that should be skipped
    node_modules = tmp_path / "node_modules" / "some_package"
    node_modules.mkdir(parents=True)
    (node_modules / "index.js").write_text("// should be skipped")

    venv = tmp_path / "venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "something.py").write_text("# should be skipped")

    return tmp_path


@pytest.fixture
def mini_python_repo(tmp_path):
    """Creates a minimal Python/FastAPI-like repo."""
    (tmp_path / "requirements.txt").write_text("""
fastapi==0.100.0
sqlalchemy==2.0.0
openai==1.0.0
pytest==7.0.0
""")
    (tmp_path / "main.py").write_text("""
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}
""")
    src = tmp_path / "src"
    src.mkdir()
    (src / "models.py").write_text("from sqlalchemy import Column, String\n")
    (src / "agents.py").write_text("import openai\n\nasync def call_llm(): pass\n")

    return tmp_path


# ─── File scorer tests ────────────────────────────────────────────────────────

def test_skip_node_modules():
    path = Path("node_modules/express/index.js")
    assert should_skip_path(path) is not None

def test_skip_venv():
    path = Path("venv/lib/python3.11/site-packages/requests/__init__.py")
    assert should_skip_path(path) is not None

def test_skip_pyc():
    path = Path("src/__pycache__/main.cpython-311.pyc")
    assert should_skip_path(path) is not None

def test_do_not_skip_source_file():
    path = Path("src/main.py")
    assert should_skip_path(path) is None

def test_do_not_skip_config():
    path = Path("dbt_project.yml")
    assert should_skip_path(path) is None

def test_walk_and_score_skips_noise(mini_dbt_repo):
    scored = walk_and_score(mini_dbt_repo)
    readable = [f for f in scored if not f.skip_reason]
    skipped = [f for f in scored if f.skip_reason]

    # node_modules and venv files should be skipped
    skipped_paths = [f.relative_path for f in skipped]
    assert any("node_modules" in p for p in skipped_paths)
    assert any("venv" in p for p in skipped_paths)

    # Core dbt files should be readable
    readable_paths = [f.relative_path for f in readable]
    assert any("dbt_project.yml" in p for p in readable_paths)
    assert any("stg_orders.sql" in p for p in readable_paths)

def test_high_value_files_score_highest(mini_dbt_repo):
    scored = walk_and_score(mini_dbt_repo)
    readable = [f for f in scored if not f.skip_reason]
    top = readable[0]
    assert "dbt_project.yml" in top.relative_path or top.is_high_value

def test_select_files_respects_budget(mini_dbt_repo):
    scored = walk_and_score(mini_dbt_repo)
    readable = [f for f in scored if not f.skip_reason]
    selected = select_files(readable, max_files=3, max_total_chars=10_000)
    assert len(selected) <= 3


# ─── Framework detector tests ─────────────────────────────────────────────────

def test_detects_dbt(mini_dbt_repo):
    paths = [str(p.relative_to(mini_dbt_repo)) for p in mini_dbt_repo.rglob("*") if p.is_file()]
    frameworks = detect_frameworks(mini_dbt_repo, paths)
    names = [f.name for f in frameworks]
    assert "dbt" in names

def test_detects_python(mini_python_repo):
    paths = [str(p.relative_to(mini_python_repo)) for p in mini_python_repo.rglob("*") if p.is_file()]
    frameworks = detect_frameworks(mini_python_repo, paths)
    names = [f.name for f in frameworks]
    assert "Python" in names
    assert "FastAPI" in names

def test_detects_openai(mini_python_repo):
    paths = [str(p.relative_to(mini_python_repo)) for p in mini_python_repo.rglob("*") if p.is_file()]
    frameworks = detect_frameworks(mini_python_repo, paths)
    names = [f.name for f in frameworks]
    assert "OpenAI API" in names

def test_no_duplicate_frameworks(mini_dbt_repo):
    paths = [str(p.relative_to(mini_dbt_repo)) for p in mini_dbt_repo.rglob("*") if p.is_file()]
    frameworks = detect_frameworks(mini_dbt_repo, paths)
    names = [f.name for f in frameworks]
    assert len(names) == len(set(names))


# ─── Local ingester tests ─────────────────────────────────────────────────────

def test_ingest_local_dbt_repo(mini_dbt_repo):
    summary = ingest_local_repo(str(mini_dbt_repo))
    assert summary.error is None
    assert summary.repo_name == mini_dbt_repo.name
    assert summary.input_type == "local"
    assert summary.total_files > 0
    assert len(summary.selected_files) > 0
    assert len(summary.frameworks) > 0
    assert summary.directory_tree != ""

def test_ingest_reads_dbt_project_yml(mini_dbt_repo):
    summary = ingest_local_repo(str(mini_dbt_repo))
    contents = [f.content for f in summary.selected_files]
    assert any("dbt_project" in c or "my_project" in c for c in contents)

def test_ingest_nonexistent_path():
    summary = ingest_local_repo("/nonexistent/path/to/repo")
    assert summary.error is not None
    assert "does not exist" in summary.error

def test_ingest_file_not_dir(tmp_path):
    f = tmp_path / "somefile.py"
    f.write_text("print('hello')")
    summary = ingest_local_repo(str(f))
    assert summary.error is not None

def test_ingest_skips_noise_dirs(mini_dbt_repo):
    summary = ingest_local_repo(str(mini_dbt_repo))
    paths = [f.relative_path for f in summary.selected_files]
    assert not any("node_modules" in p for p in paths)
    assert not any("venv" in p for p in paths)


# ─── Ingester router tests ─────────────────────────────────────────────────────

def test_is_github_url():
    assert is_github_url("https://github.com/owner/repo") is True
    assert is_github_url("https://github.com/owner/repo.git") is True
    assert is_github_url("/local/path/to/repo") is False
    assert is_github_url("~/projects/myrepo") is False

def test_ingest_repo_routes_local(mini_python_repo):
    summary = ingest_repo(str(mini_python_repo))
    assert summary.input_type == "local"
    assert summary.error is None

def test_format_summary_for_llm(mini_dbt_repo):
    summary = ingest_local_repo(str(mini_dbt_repo))
    formatted = format_summary_for_llm(summary)
    assert "Repository:" in formatted
    assert "Detected technologies:" in formatted
    assert "Directory structure:" in formatted
    assert "Selected files" in formatted
    assert len(formatted) > 100
