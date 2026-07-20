"""
Eval test cases for the curiosity breaker agent.

Starting with one concrete case as agreed with Sudeep Sir:
- Concept: dbt testing strategy
- Goal: interview

Each test case defines:
- The input to the agent
- An example of an acceptable output
- An example of an unacceptable output
- The objective checks that apply
- The LLM judge rubric thresholds
"""

TEST_CASES = [
    {
        "id": "tc_dbt_testing_interview",
        "description": "dbt testing strategy gap for interview preparation",

        "input": {
            "concept": "dbt testing strategy",
            "learning_goal": "interview",
            "domain": "data pipeline",
            "repo_context": (
                "A dbt project with 12 models for e-commerce analytics. "
                "Models include staging, intermediate, and mart layers. "
                "No schema.yml test files exist in the repository."
            ),
        },

        # An example of what a good anecdote looks like.
        # Used as a reference for the LLM judge — not as a required exact match.
        "example_acceptable": (
            "Your pipeline ran successfully every day for 3 months. "
            "Last Tuesday, a senior engineer asked during your interview: "
            "'Your orders model showed 40,000 rows on Monday and 12 on Tuesday. "
            "How would you have caught that automatically?' "
            "You had no answer."
        ),

        # An example of what a bad anecdote looks like.
        # Used to calibrate the LLM judge and explain the objective checks.
        "example_unacceptable": (
            "Testing is important in dbt. Without schema tests, "
            "your data quality will suffer. You should add not_null "
            "and unique tests to your models to ensure correctness."
        ),

        # Why the unacceptable example fails
        "unacceptable_reason": (
            "Explains the concept directly, suggests a solution, "
            "no concrete scenario, no curiosity created."
        ),

        # Objective eval config for this test case
        "objective_checks": {
            "min_words": 30,
            "max_words": 150,
            "forbidden_phrases": [
                "you should",
                "the solution is",
                "the reason is",
                "this is because",
                "this happens when",
                "to fix this",
                "schema test",
                "not_null",
                "unique test",
                "dbt test",
            ],
            "must_contain_concrete_detail": True,  # digit, entity, or observable event
        },

        # LLM judge rubric thresholds (each dimension scored 1-5)
        "llm_judge_thresholds": {
            "curiosity": 4,        # Must strongly create curiosity
            "relevance": 4,        # Must clearly relate to dbt testing
            "realism": 3,          # Should feel plausible
            "non_explanatory": 4,  # Must not give away the answer
            "goal_alignment": 4,   # Must feel like an interview scenario
            "total_minimum": 18,   # Out of 25
        },
    }
]
