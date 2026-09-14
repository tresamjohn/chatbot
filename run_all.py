import argparse

from generate_testcases import generate_testcases
from execute_chatbot import execute_testcases
from evaluate_results import evaluate_results
from generate_report import generate_report


def parse_arguments():

    parser = argparse.ArgumentParser(
        description="AI Chatbot Automation Framework"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of test cases to generate.",
    )

    parser.add_argument(
        "--strategy",
        nargs="+",
        default=None,
        help=(
            "Generation strategies. Example: "
            "--strategy direct conversational short "
            "or --strategy all"
        ),
    )

    return parser.parse_args()


def main():

    args = parse_arguments()

    print("=" * 60)
    print("AI CHATBOT AUTOMATION FRAMEWORK")
    print("=" * 60)

    if args.count is not None:
        print(
            f"\nRequested test cases: {args.count}"
        )

    if args.strategy:
        print(
            "Requested strategies: "
            + ", ".join(
                strategy.upper()
                for strategy in args.strategy
            )
        )

    # ========================================================
    # STAGE 1 - GENERATION
    # ========================================================

    print()
    print("[STAGE 1] TEST CASE GENERATION")
    print("-" * 60)

    generate_testcases(
        count=args.count,
        strategies=args.strategy,
    )

    # ========================================================
    # STAGE 2 - EXECUTION
    # ========================================================

    print()
    print("[STAGE 2] CHATBOT EXECUTION")
    print("-" * 60)

    execute_testcases()

    # ========================================================
    # STAGE 3 - EVALUATION
    # ========================================================

    print()
    print("[STAGE 3] RESPONSE EVALUATION")
    print("-" * 60)

    evaluate_results()

    # ========================================================
    # STAGE 4 - REPORTING
    # ========================================================

    print()
    print("[STAGE 4] REPORT GENERATION")
    print("-" * 60)

    generate_report()

    # ========================================================
    # COMPLETE
    # ========================================================

    print()
    print("=" * 60)
    print("AUTOMATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()