"""
Test generation strategies.

Each strategy describes how the LLM should transform a
knowledge-base fact into a chatbot test question.
"""


STRATEGIES = {

    "direct": """
Ask a simple, direct factual question.

Example:
Fact: The capital of France is Paris.
Question: What is the capital of France?
""",

    "rephrased": """
Ask the same factual question using different wording.

Example:
Fact: The capital of France is Paris.
Question: Which city is the capital of France?
""",

    "conversational": """
Ask the question naturally, as if a person were talking
to a chatbot.

Example:
Fact: The capital of France is Paris.
Question: Could you tell me what France's capital is?
""",

    "short": """
Ask an extremely short question while keeping the meaning
understandable.

Example:
Fact: The capital of France is Paris.
Question: France capital?
""",

    "verbose": """
Ask a longer question containing unnecessary but harmless
context. The factual question must remain clear.

Example:
Fact: The capital of France is Paris.
Question: I am trying to remember the name of the city that
serves as the capital of France. What is it?
""",

    "typo": """
Introduce one or two realistic spelling or typing mistakes
while keeping the question understandable.

Example:
Fact: The capital of France is Paris.
Question: Wat is the capital of Frnace?
""",

    "case_variation": """
Use unusual capitalization while preserving the question.

Example:
Fact: The capital of France is Paris.
Question: WHAT IS THE CAPITAL OF FRANCE?
""",

    "contextual": """
Place the factual question inside a realistic context or
scenario.

Example:
Fact: The capital of France is Paris.
Question: I'm planning a trip to France. What is its capital city?
""",
}


ALL_STRATEGIES = list(STRATEGIES.keys())


def validate_strategies(selected):
    """
    Validate strategy names supplied by the user.
    """

    invalid = [
        strategy
        for strategy in selected
        if strategy not in STRATEGIES
    ]

    if invalid:
        raise ValueError(
            "Unknown strategy/strategies: "
            + ", ".join(invalid)
        )

    return selected


def get_strategy_prompt(strategy):
    """
    Return the prompt instructions for a strategy.
    """

    if strategy not in STRATEGIES:
        raise ValueError(
            f"Unknown strategy: {strategy}"
        )

    return STRATEGIES[strategy]