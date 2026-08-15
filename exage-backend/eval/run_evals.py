"""
Eval runner for curiosity breaker anecdotes.

Runs the full eval pipeline for one or all test cases:
1. Generate an anecdote using the curiosity breaker agent
2. Run objective checks (free, fast)
3. Run LLM judge (costs API calls) — only if objective passes or --force

Usage:
    # Run all test cases, objective only (free)
    python -m eval.run_evals --mode objective

    # Run all test cases, full eval including LLM judge
    python -m eval.run_evals --mode full

    # Run a specific test case
    python -m eval.run_evals --case tc_dbt_testing_interview

    # Run with a custom anecdote (skip generation, just evaluate)
    python -m eval.run_evals --anecdote "Your pipeline ran fine for 3 months..."
"""

import asyncio
import argparse
import json
from eval.test_cases import TEST_CASES
from eval.objective_eval import run_objective_eval, format_objective_result
from eval.llm_judge import run_llm_judge, format_judge_result
from chat_agents.curiosity_breaker import run_curiosity_breaker


async def run_single_eval(
    test_case: dict,
    mode: str = "full",
    custom_anecdote: str | None = None,
) -> dict:
    """
    Run eval for a single test case.

    Args:
        test_case: one entry from TEST_CASES
        mode: "objective" (no API) | "full" (includes LLM judge)
        custom_anecdote: if provided, skip generation and evaluate this text

    Returns:
        dict with full eval results
    """
    tc_id = test_case["id"]
    inp = test_case["input"]

    print(f"\n{'='*60}")
    print(f"Test case: {tc_id}")
    print(f"Concept:   {inp['concept']}")
    print(f"Goal:      {inp['learning_goal']}")
    print(f"Mode:      {mode}")
    print(f"{'='*60}")

    # Step 1: generate or use provided anecdote
    if custom_anecdote:
        anecdote = custom_anecdote
        gen_latency = 0
        print(f"\nUsing provided anecdote ({len(anecdote.split())} words)")
    else:
        print("\nGenerating anecdote...")
        anecdote, gen_latency = await run_curiosity_breaker(
            concept=inp["concept"],
            learning_goal=inp["learning_goal"],
            domain=inp["domain"],
            repo_context=inp["repo_context"],
        )
        print(f"Generated in {gen_latency}ms")

    print(f"\nAnecdote:\n\"{anecdote}\"\n")

    # Step 2: objective eval (always runs)
    obj_result = run_objective_eval(
        anecdote=anecdote,
        checks=test_case.get("objective_checks"),
    )
    print(format_objective_result(obj_result))

    results = {
        "test_case_id": tc_id,
        "anecdote": anecdote,
        "generation_latency_ms": gen_latency,
        "objective": {
            "passed": obj_result.passed,
            "checks_passed": obj_result.checks_passed,
            "total_checks": obj_result.total_checks,
            "failure_reasons": obj_result.failure_reasons,
        },
        "llm_judge": None,
    }

    # Step 3: LLM judge (only in full mode, or if objective fails and we want to see why)
    if mode == "full":
        print("\nRunning LLM judge...")
        judge_result = await run_llm_judge(
            anecdote=anecdote,
            concept=inp["concept"],
            learning_goal=inp["learning_goal"],
            domain=inp["domain"],
            example_acceptable=test_case["example_acceptable"],
            example_unacceptable=test_case["example_unacceptable"],
            thresholds=test_case.get("llm_judge_thresholds"),
        )
        print(format_judge_result(judge_result))

        results["llm_judge"] = {
            "passed": judge_result.passed,
            "total": judge_result.total,
            "threshold": judge_result.threshold,
            "scores": {
                "curiosity": judge_result.curiosity,
                "relevance": judge_result.relevance,
                "realism": judge_result.realism,
                "non_explanatory": judge_result.non_explanatory,
                "goal_alignment": judge_result.goal_alignment,
            },
            "reasoning": judge_result.reasoning,
            "strongest_aspect": judge_result.strongest_aspect,
            "weakest_aspect": judge_result.weakest_aspect,
            "latency_ms": judge_result.latency_ms,
        }

    # Overall verdict
    if mode == "full":
        overall_pass = obj_result.passed and judge_result.passed
    else:
        overall_pass = obj_result.passed

    results["overall_pass"] = overall_pass
    print(f"\nOverall: {'✅ PASS' if overall_pass else '❌ FAIL'}")

    return results


async def main():
    parser = argparse.ArgumentParser(description="Run curiosity breaker evals")
    parser.add_argument(
        "--mode",
        choices=["objective", "full"],
        default="full",
        help="objective = code checks only (free). full = includes LLM judge (costs API calls)"
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Run a specific test case by ID. Runs all if not specified."
    )
    parser.add_argument(
        "--anecdote",
        type=str,
        default=None,
        help="Skip generation and evaluate this anecdote text directly"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Save results to a JSON file"
    )
    args = parser.parse_args()

    # Select test cases to run
    if args.case:
        cases = [tc for tc in TEST_CASES if tc["id"] == args.case]
        if not cases:
            print(f"Test case '{args.case}' not found.")
            print(f"Available: {[tc['id'] for tc in TEST_CASES]}")
            return
    else:
        cases = TEST_CASES

    print(f"Running {len(cases)} test case(s) in '{args.mode}' mode")

    all_results = []
    for tc in cases:
        result = await run_single_eval(
            test_case=tc,
            mode=args.mode,
            custom_anecdote=args.anecdote,
        )
        all_results.append(result)

    # Summary
    total = len(all_results)
    passed = sum(1 for r in all_results if r["overall_pass"])
    print(f"\n{'='*60}")
    print(f"Summary: {passed}/{total} passed")
    print(f"{'='*60}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"Results saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
