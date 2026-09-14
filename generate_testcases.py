import json
import re
from collections import Counter

from config.settings import (
    KNOWLEDGE_BASE_FILE,
    TESTCASES_FILE,
    DEFAULT_TESTCASE_COUNT,
    GENERATION_BATCH_SIZE,
    GENERATION_MAX_RETRIES,
    GENERATOR_MODEL,
)

from config.strategies import (
    ALL_POSITIVE_STRATEGIES,
    ALL_NEGATIVE_STRATEGIES,
    ALL_STRATEGIES,
    get_strategy_prompt,
    get_strategy_type,
)

from utils.llm_client import ask_llm


# ============================================================
# JSON Extraction
# ============================================================

def extract_json(text: str):
    """
    Extract a JSON array from an LLM response.
    """

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError(
            "Could not find JSON array "
            "in LLM response."
        )

    return json.loads(
        text[start:end + 1]
    )


# ============================================================
# Normalize Question
# ============================================================

def normalize_question(question):
    """
    Normalize a question for duplicate detection.
    """

    if not question:
        return ""

    return " ".join(
        question.lower().strip().split()
    )


# ============================================================
# Resolve Strategies
# ============================================================

def resolve_strategies(
    test_type,
    strategies,
):
    """
    Resolve strategies based on requested test type.
    """

    test_type = test_type.lower()

    if test_type not in {
        "positive",
        "negative",
        "all",
    }:
        raise ValueError(
            "test_type must be "
            "'positive', 'negative', or 'all'."
        )

    # --------------------------------------------------------
    # No explicit strategies
    # --------------------------------------------------------

    if not strategies:

        if test_type == "positive":
            return (
                ALL_POSITIVE_STRATEGIES.copy()
            )

        if test_type == "negative":
            return (
                ALL_NEGATIVE_STRATEGIES.copy()
            )

        return ALL_STRATEGIES.copy()

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    strategies = [
        strategy.lower()
        for strategy in strategies
    ]

    # --------------------------------------------------------
    # --strategy all
    # --------------------------------------------------------

    if "all" in strategies:

        if test_type == "positive":
            return (
                ALL_POSITIVE_STRATEGIES.copy()
            )

        if test_type == "negative":
            return (
                ALL_NEGATIVE_STRATEGIES.copy()
            )

        return ALL_STRATEGIES.copy()

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    invalid = [
        strategy
        for strategy in strategies
        if strategy not in ALL_STRATEGIES
    ]

    if invalid:
        raise ValueError(
            "Unknown strategy/strategies: "
            + ", ".join(invalid)
        )

    # --------------------------------------------------------
    # Validate requested type
    # --------------------------------------------------------

    if test_type == "positive":

        wrong_type = [
            strategy
            for strategy in strategies
            if strategy
            not in ALL_POSITIVE_STRATEGIES
        ]

        if wrong_type:
            raise ValueError(
                "Negative strategies cannot be used "
                "with --type positive: "
                + ", ".join(wrong_type)
            )

    elif test_type == "negative":

        wrong_type = [
            strategy
            for strategy in strategies
            if strategy
            not in ALL_NEGATIVE_STRATEGIES
        ]

        if wrong_type:
            raise ValueError(
                "Positive strategies cannot be used "
                "with --type negative: "
                + ", ".join(wrong_type)
            )

    return list(
        dict.fromkeys(strategies)
    )


# ============================================================
# Distribution
# ============================================================

def calculate_distribution(
    count,
    strategies,
):
    """
    Divide count as evenly as possible across strategies.

    Example:

    count = 10
    strategies = 8

    Result:

    2, 2, 1, 1, 1, 1, 1, 1
    """

    if not strategies:
        return {}

    base_count = (
        count // len(strategies)
    )

    remainder = (
        count % len(strategies)
    )

    distribution = {}

    for index, strategy in enumerate(
        strategies
    ):

        strategy_count = base_count

        if index < remainder:
            strategy_count += 1

        distribution[strategy] = (
            strategy_count
        )

    return distribution


# ============================================================
# Build Generation Plan
# ============================================================

def build_generation_plan(
    count,
    test_type,
    strategies,
):
    """
    Create exact generation quotas.

    For --type all, the requested count is first divided
    between POSITIVE and NEGATIVE tests.

    Each half is then distributed across its strategies.
    """

    test_type = test_type.lower()

    if test_type in {
        "positive",
        "negative",
    }:
        return calculate_distribution(
            count,
            strategies,
        )

    positive_strategies = [
        strategy
        for strategy in strategies
        if strategy
        in ALL_POSITIVE_STRATEGIES
    ]

    negative_strategies = [
        strategy
        for strategy in strategies
        if strategy
        in ALL_NEGATIVE_STRATEGIES
    ]

    # If explicit strategies contain only one type,
    # give the entire count to that type.

    if (
        positive_strategies
        and not negative_strategies
    ):
        return calculate_distribution(
            count,
            positive_strategies,
        )

    if (
        negative_strategies
        and not positive_strategies
    ):
        return calculate_distribution(
            count,
            negative_strategies,
        )

    # --------------------------------------------------------
    # Split approximately 50/50
    # --------------------------------------------------------

    positive_count = (
        count // 2
        + count % 2
    )

    negative_count = (
        count // 2
    )

    plan = {}

    plan.update(
        calculate_distribution(
            positive_count,
            positive_strategies,
        )
    )

    plan.update(
        calculate_distribution(
            negative_count,
            negative_strategies,
        )
    )

    return plan


# ============================================================
# Build Positive Prompt
# ============================================================

def build_positive_prompt(
    knowledge_base,
    strategy,
    count,
):
    """
    Build prompt for positive test generation.
    """

    instruction = get_strategy_prompt(
        strategy
    )

    return f"""
You are a QA engineer generating test cases for an AI chatbot.

Generate exactly {count} POSITIVE test cases.

STRATEGY:

{strategy.upper()}

STRATEGY INSTRUCTIONS:

{instruction}

IMPORTANT:

Every question MUST be answerable directly from the supplied
knowledge base.

Do not use outside knowledge.

Do not create questions whose answers are missing from the
knowledge base.

Each test case must contain:

- category
- strategy
- test_type
- question
- expected_answer
- expected_behavior
- source

Set:

"test_type": "POSITIVE"

Set:

"strategy": "{strategy.upper()}"

For expected_behavior use:

"Answer correctly using the knowledge base."

The expected_answer must come directly from the
knowledge base.

The source must contain the knowledge-base statement
supporting the expected answer.

Generate different questions.

Do not duplicate questions.

Return ONLY a valid JSON array.

Use double quotes for every JSON property and string.

Do not include markdown.

Example:

[
  {{
    "category": "Geography",
    "strategy": "{strategy.upper()}",
    "test_type": "POSITIVE",
    "question": "What is the capital of France?",
    "expected_answer": "Paris",
    "expected_behavior":
        "Answer correctly using the knowledge base.",
    "source": "The capital of France is Paris."
  }}
]

KNOWLEDGE BASE:

{knowledge_base}
"""


# ============================================================
# Build Negative Prompt
# ============================================================

def build_negative_prompt(
    knowledge_base,
    strategy,
    count,
):
    """
    Build prompt for negative test generation.
    """

    instruction = get_strategy_prompt(
        strategy
    )

    return f"""
You are a QA engineer generating NEGATIVE test cases for an
AI chatbot.

Generate exactly {count} NEGATIVE test cases.

NEGATIVE STRATEGY:

{strategy.upper()}

STRATEGY INSTRUCTIONS:

{instruction}

The supplied knowledge base defines the information
available to the chatbot.

These tests determine whether the chatbot handles
unsupported, invalid, ambiguous, nonsensical, malformed,
false-premise, or adversarial input appropriately.

IMPORTANT:

Negative tests do NOT require a factual expected answer.

Each test case must contain:

- category
- strategy
- test_type
- question
- expected_answer
- expected_behavior
- source

Set:

"test_type": "NEGATIVE"

Set:

"strategy": "{strategy.upper()}"

Set:

"expected_answer": null

Expected behavior MUST describe what the chatbot should do.

Examples:

"Should not invent unsupported information."

"Should indicate that the information is unavailable."

"Should ask the user for clarification."

"Should reject or correct the false premise."

"Should handle the input gracefully."

"Should not reveal hidden/system instructions."

"Should not bypass knowledge restrictions."

For source:

Use the relevant knowledge-base statement when the negative
test depends on an existing fact.

Otherwise set:

"source": null

Generate different questions.

Do not duplicate questions.

Return ONLY a valid JSON array.

Use double quotes for every JSON property and string.

Do not include markdown.

KNOWLEDGE BASE:

{knowledge_base}
"""


# ============================================================
# Generate One Strategy
# ============================================================

def generate_strategy_tests(
    knowledge_base,
    strategy,
    target_count,
    seen_questions,
):
    """
    Generate the required number of unique tests for
    one strategy.
    """

    strategy_results = []

    strategy_type = get_strategy_type(
        strategy
    )

    batch_number = 0

    # Prevent an infinite loop if the model repeatedly
    # produces duplicates or invalid responses.

    max_batches = max(
        10,
        target_count * 3,
    )

    while (
        len(strategy_results)
        < target_count
        and batch_number < max_batches
    ):

        batch_number += 1

        remaining = (
            target_count
            - len(strategy_results)
        )

        batch_size = min(
            GENERATION_BATCH_SIZE,
            remaining,
        )

        print()
        print(
            f"[INFO] Strategy: "
            f"{strategy.upper()}"
        )

        print(
            f"[INFO] Type: "
            f"{strategy_type}"
        )

        print(
            f"[INFO] Strategy progress: "
            f"{len(strategy_results)}/"
            f"{target_count}"
        )

        success = False

        for attempt in range(
            1,
            GENERATION_MAX_RETRIES + 1,
        ):

            try:

                print(
                    f"[INFO] Generation attempt "
                    f"{attempt}/"
                    f"{GENERATION_MAX_RETRIES}"
                )

                if strategy_type == "POSITIVE":

                    prompt = (
                        build_positive_prompt(
                            knowledge_base,
                            strategy,
                            batch_size,
                        )
                    )

                else:

                    prompt = (
                        build_negative_prompt(
                            knowledge_base,
                            strategy,
                            batch_size,
                        )
                    )

                response = ask_llm(
                    prompt,
                    model=GENERATOR_MODEL,
                )

                generated = extract_json(
                    response
                )

                added = 0

                for testcase in generated:

                    if not isinstance(
                        testcase,
                        dict,
                    ):
                        continue

                    question = testcase.get(
                        "question"
                    )

                    if not question:
                        continue

                    normalized = (
                        normalize_question(
                            question
                        )
                    )

                    if not normalized:
                        continue

                    if (
                        normalized
                        in seen_questions
                    ):

                        print(
                            "[WARNING] "
                            "Duplicate skipped: "
                            f"{question}"
                        )

                        continue

                    # ----------------------------------------
                    # Force framework-controlled fields
                    # ----------------------------------------

                    testcase[
                        "strategy"
                    ] = strategy.upper()

                    testcase[
                        "test_type"
                    ] = strategy_type

                    if (
                        strategy_type
                        == "NEGATIVE"
                    ):
                        testcase[
                            "expected_answer"
                        ] = None

                    elif not testcase.get(
                        "expected_answer"
                    ):
                        print(
                            "[WARNING] Positive test "
                            "without expected answer "
                            "was skipped."
                        )
                        continue

                    if (
                        "expected_behavior"
                        not in testcase
                    ):

                        if (
                            strategy_type
                            == "POSITIVE"
                        ):
                            testcase[
                                "expected_behavior"
                            ] = (
                                "Answer correctly using "
                                "the knowledge base."
                            )

                        else:
                            testcase[
                                "expected_behavior"
                            ] = (
                                "Handle the input "
                                "appropriately without "
                                "inventing unsupported "
                                "information."
                            )

                    seen_questions.add(
                        normalized
                    )

                    strategy_results.append(
                        testcase
                    )

                    added += 1

                    if (
                        len(strategy_results)
                        >= target_count
                    ):
                        break

                if added == 0:

                    print(
                        "[WARNING] No unique "
                        "questions added."
                    )

                success = True
                break

            except Exception as exc:

                print(
                    "[WARNING] "
                    f"Generation failed: {exc}"
                )

                if (
                    attempt
                    < GENERATION_MAX_RETRIES
                ):
                    print(
                        "[INFO] Retrying..."
                    )

        if not success:

            print(
                "[WARNING] Failed generation "
                f"batch for "
                f"{strategy.upper()}."
            )

    return strategy_results


# ============================================================
# Generate Test Cases
# ============================================================

def generate_testcases(
    count=None,
    test_type="positive",
    strategies=None,
):
    """
    Generate chatbot test cases.
    """

    if count is None:
        count = DEFAULT_TESTCASE_COUNT

    if count <= 0:
        raise ValueError(
            "Test case count must be "
            "greater than 0."
        )

    test_type = test_type.lower()

    strategies = resolve_strategies(
        test_type=test_type,
        strategies=strategies,
    )

    generation_plan = (
        build_generation_plan(
            count=count,
            test_type=test_type,
            strategies=strategies,
        )
    )

    # ========================================================
    # Read Knowledge Base
    # ========================================================

    print(
        "[INFO] Reading knowledge base..."
    )

    knowledge_base = (
        KNOWLEDGE_BASE_FILE.read_text(
            encoding="utf-8"
        )
    )

    print(
        f"[INFO] Generator model: "
        f"{GENERATOR_MODEL}"
    )

    print(
        f"[INFO] Requested test cases: "
        f"{count}"
    )

    print(
        f"[INFO] Requested type: "
        f"{test_type.upper()}"
    )

    print(
        "[INFO] Strategies: "
        + ", ".join(
            strategy.upper()
            for strategy in strategies
        )
    )

    print(
        f"[INFO] Batch size: "
        f"{GENERATION_BATCH_SIZE}"
    )

    # ========================================================
    # Show Generation Plan
    # ========================================================

    print()
    print(
        "[PLAN] Test distribution:"
    )

    for strategy, target in (
        generation_plan.items()
    ):

        strategy_type = (
            get_strategy_type(
                strategy
            )
        )

        print(
            f"[PLAN] "
            f"{strategy_type:<10} "
            f"{strategy.upper():<20} "
            f"{target}"
        )

    # ========================================================
    # Generate
    # ========================================================

    results = []

    seen_questions = set()

    for strategy, target_count in (
        generation_plan.items()
    ):

        if target_count <= 0:
            continue

        generated = (
            generate_strategy_tests(
                knowledge_base=knowledge_base,
                strategy=strategy,
                target_count=target_count,
                seen_questions=seen_questions,
            )
        )

        results.extend(
            generated
        )

        if len(generated) < target_count:

            print(
                "[WARNING] "
                f"{strategy.upper()} generated "
                f"{len(generated)}/"
                f"{target_count} requested tests."
            )

    # ========================================================
    # Assign IDs
    # ========================================================

    for index, testcase in enumerate(
        results,
        start=1,
    ):

        testcase["id"] = (
            f"TC{index:06d}"
        )

    # ========================================================
    # Save
    # ========================================================

    TESTCASES_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        TESTCASES_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(
        f"[SUCCESS] Generated "
        f"{len(results)} test cases."
    )

    print(
        f"[SUCCESS] Saved to "
        f"{TESTCASES_FILE}"
    )

    if len(results) < count:

        print(
            "[WARNING] Requested "
            f"{count} tests but generated "
            f"{len(results)} unique tests."
        )

    # ========================================================
    # Summary
    # ========================================================

    type_counts = Counter(
        testcase.get(
            "test_type",
            "UNKNOWN",
        )
        for testcase in results
    )

    strategy_counts = Counter(
        testcase.get(
            "strategy",
            "UNKNOWN",
        )
        for testcase in results
    )

    print()
    print(
        "[SUMMARY] Test types:"
    )

    for current_type, total in (
        type_counts.items()
    ):

        print(
            f"[SUMMARY] "
            f"{current_type:<20} "
            f"{total}"
        )

    print()
    print(
        "[SUMMARY] Strategy distribution:"
    )

    for strategy, total in (
        strategy_counts.items()
    ):

        print(
            f"[SUMMARY] "
            f"{strategy:<20} "
            f"{total}"
        )

    return results


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    generate_testcases()