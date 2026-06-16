"""
Real-data test script for the Option 2 pipeline.

Runs the full pipeline (Repo Ingester → Concept Extractor → Skill Inferrer
→ Gap Detector → Consequence Ranker) against a real repository using
real OpenAI API calls.

Usage:
    python test_option2_real.py

Requires:
    - .env file with OPENAI_API_KEY set (same as the rest of exage-backend)
    - Internet access (for GitHub API calls)
"""

import asyncio
import json
import sys
from agents_option2.pipeline_v2 import run_option2_pipeline, format_result_for_display, result_to_session_context


REPO_URL = "https://github.com/meghana-gajendran/docksmith"
LEARNING_GOAL = "interview"  # change to: project | teaching | exam | curiosity


async def main():
    print(f"Analysing: {REPO_URL}")
    print(f"Learning goal: {LEARNING_GOAL}")
    print("Running pipeline (this makes 4 real LLM calls, may take 30-60s)...")
    print("-" * 60)

    result = await run_option2_pipeline(REPO_URL, learning_goal=LEARNING_GOAL)

    if result.error:
        print(f"ERROR: {result.error}")
        sys.exit(1)

    # ── Human-readable summary ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("HUMAN-READABLE SUMMARY")
    print("=" * 60)
    print(format_result_for_display(result))

    # ── Agent traces (timing + counts) ──────────────────────────────
    print("\n" + "=" * 60)
    print("AGENT TRACES")
    print("=" * 60)
    for trace in result.agent_traces:
        print(json.dumps(trace, indent=2))

    # ── Full raw output (for debugging) ──────────────────────────────
    print("\n" + "=" * 60)
    print("EXTRACTED CONCEPTS (raw)")
    print("=" * 60)
    print(json.dumps(result.extracted_concepts, indent=2))

    print("\n" + "=" * 60)
    print("SKILL MAP (raw)")
    print("=" * 60)
    print(json.dumps(result.skill_map, indent=2))

    print("\n" + "=" * 60)
    print("RAW GAPS (before ranking)")
    print("=" * 60)
    print(json.dumps(result.raw_gaps, indent=2))

    print("\n" + "=" * 60)
    print("RANKED GAPS (final output)")
    print("=" * 60)
    for gap in result.ranked_gaps:
        print(f"\nRank {gap.rank}: {gap.concept} [{gap.urgency}] ({gap.gap_type})")
        print(f"  Why it matters: {gap.consequence_for_goal}")
        print(f"  Probing question: {gap.probing_question}")
        print(f"  Good answer shows: {gap.what_a_good_answer_shows}")

    # ── Session context (what gets passed to Option 1 chat) ──────────
    print("\n" + "=" * 60)
    print("SESSION CONTEXT (for Option 1 handoff)")
    print("=" * 60)
    context = result_to_session_context(result)
    print(json.dumps(context, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
