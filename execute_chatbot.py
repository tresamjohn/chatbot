import json
import time

from config.settings import (
    TESTCASES_FILE,
    EXECUTION_RESULTS_FILE,
    TARGET_CHATBOT_MODEL,
)

from utils.llm_client import ask_llm


def execute_testcases():

    print("[INFO] Reading test cases...")

    if not TESTCASES_FILE.exists():
        raise FileNotFoundError(
            f"Test cases file not found: {TESTCASES_FILE}"
        )

    with open(
        TESTCASES_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        testcases = json.load(file)

    print(f"[INFO] Found {len(testcases)} test cases.")
    print(f"[INFO] Target model: {TARGET_CHATBOT_MODEL}")

    EXECUTION_RESULTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Start a fresh execution result file
    with open(
        EXECUTION_RESULTS_FILE,
        "w",
        encoding="utf-8",
    ):
        pass

    successful = 0
    failed = 0

    for index, testcase in enumerate(
        testcases,
        start=1,
    ):

        testcase_id = testcase.get(
            "id",
            f"TC{index:05d}",
        )

        question = testcase["question"]

        print(
            f"[INFO] Executing {index}/{len(testcases)} "
            f"- {testcase_id}"
        )

        start_time = time.perf_counter()

        actual_answer = None
        error = None
        execution_status = "SUCCESS"

        try:

            actual_answer = ask_llm(
                question,
                model=TARGET_CHATBOT_MODEL,
            )

            successful += 1

        except Exception as exc:

            execution_status = "FAILED"
            error = str(exc)
            failed += 1

            print(
                f"[ERROR] {testcase_id} - {error}"
            )

        response_time = round(
            time.perf_counter() - start_time,
            2,
        )

        result = {
    "id": testcase_id,
    "category": testcase.get("category"),
    "test_type": testcase.get("test_type"),
    "strategy": testcase.get("strategy"),
    "question": question,
    "expected_answer": testcase.get(
        "expected_answer"
    ),
    "expected_behavior": testcase.get(
        "expected_behavior"
    ),
    "actual_answer": actual_answer,
    "source": testcase.get("source"),
    "target_model": TARGET_CHATBOT_MODEL,
    "execution_status": execution_status,
    "response_time_seconds": response_time,
    "error": error,
}

        # Save immediately after each testcase
        with open(
            EXECUTION_RESULTS_FILE,
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )

        if execution_status == "SUCCESS":
            print(
                f"[SUCCESS] {testcase_id} "
                f"({response_time}s)"
            )

    print()
    print("[SUCCESS] Chatbot execution completed.")
    print(f"[SUMMARY] Total      : {len(testcases)}")
    print(f"[SUMMARY] Successful : {successful}")
    print(f"[SUMMARY] Failed     : {failed}")

    print(
        f"[SUCCESS] Results saved to "
        f"{EXECUTION_RESULTS_FILE}"
    )


if __name__ == "__main__":
    execute_testcases()