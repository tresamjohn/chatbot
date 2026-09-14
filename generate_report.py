import json
from html import escape

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from config.settings import (
    EVALUATED_RESULTS_FILE,
    REPORT_FILE,
    HTML_REPORT_FILE,
)


# ============================================================
# Read Evaluated Results
# ============================================================

def read_evaluated_results():

    if not EVALUATED_RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Evaluated results not found: "
            f"{EVALUATED_RESULTS_FILE}"
        )

    results = []

    with open(
        EVALUATED_RESULTS_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            if line.strip():
                results.append(json.loads(line))

    return results


# ============================================================
# Helper Functions
# ============================================================

def get_evaluation_result(result):
    """
    Supports both new and old result field names.
    """

    return (
        result.get("evaluation_result")
        or result.get("result")
        or "UNKNOWN"
    )


def get_evaluation_reason(result):
    """
    Supports both new and old reason field names.
    """

    return (
        result.get("evaluation_reason")
        or result.get("reason")
        or ""
    )


def get_evaluator_model(result):
    """
    Supports both evaluator_model and evaluation_model.
    """

    return (
        result.get("evaluator_model")
        or result.get("evaluation_model")
        or ""
    )


def display_value(value, default="N/A"):
    """
    Prevent None or empty values appearing in reports.
    """

    if value is None:
        return default

    if isinstance(value, str) and not value.strip():
        return default

    return value


# ============================================================
# Excel Report
# ============================================================

def generate_excel_report(results):

    print("[INFO] Generating Excel report...")

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    workbook = Workbook()

    sheet = workbook.active
    sheet.title = "Chatbot Test Results"

    # --------------------------------------------------------
    # Headers
    # --------------------------------------------------------

    headers = [
        "Test ID",
        "Test Type",
        "Strategy",
        "Category",
        "Question",
        "Expected Answer",
        "Expected Behavior",
        "Actual Answer",
        "Result",
        "Reason",
        "Target Model",
        "Evaluator Model",
        "Response Time (Seconds)",
        "Knowledge Base Source",
    ]

    sheet.append(headers)

    # --------------------------------------------------------
    # Header formatting
    # --------------------------------------------------------

    for cell in sheet[1]:

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    # --------------------------------------------------------
    # Add result rows
    # --------------------------------------------------------

    for result in results:

        evaluation_result = get_evaluation_result(
            result
        )

        evaluation_reason = get_evaluation_reason(
            result
        )

        evaluator_model = get_evaluator_model(
            result
        )

        sheet.append([
            display_value(
                result.get("id")
            ),

            display_value(
                result.get("test_type")
            ),

            display_value(
                result.get("strategy")
            ),

            display_value(
                result.get("category")
            ),

            display_value(
                result.get("question")
            ),

            display_value(
                result.get("expected_answer")
            ),

            display_value(
                result.get("expected_behavior")
            ),

            display_value(
                result.get("actual_answer")
            ),

            evaluation_result,

            evaluation_reason,

            display_value(
                result.get("target_model")
            ),

            display_value(
                evaluator_model
            ),

            display_value(
                result.get("response_time_seconds")
            ),

            display_value(
                result.get("source")
            ),
        ])

    # --------------------------------------------------------
    # PASS / FAIL formatting
    #
    # Result column is column 9
    # --------------------------------------------------------

    for row in range(
        2,
        sheet.max_row + 1,
    ):

        result_cell = sheet.cell(
            row=row,
            column=9,
        )

        if result_cell.value == "PASS":

            result_cell.fill = PatternFill(
                fill_type="solid",
                fgColor="C6EFCE",
            )

        elif result_cell.value == "FAIL":

            result_cell.fill = PatternFill(
                fill_type="solid",
                fgColor="FFC7CE",
            )

        else:

            result_cell.fill = PatternFill(
                fill_type="solid",
                fgColor="FFEB9C",
            )

        result_cell.font = Font(
            bold=True
        )

    # --------------------------------------------------------
    # Wrap text
    # --------------------------------------------------------

    for row in sheet.iter_rows():

        for cell in row:

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

    # --------------------------------------------------------
    # Column widths
    # --------------------------------------------------------

    column_widths = {
        1: 12,   # Test ID
        2: 15,   # Test Type
        3: 18,   # Strategy
        4: 18,   # Category
        5: 40,   # Question
        6: 30,   # Expected Answer
        7: 50,   # Expected Behavior
        8: 60,   # Actual Answer
        9: 12,   # Result
        10: 60,  # Reason
        11: 28,  # Target Model
        12: 32,  # Evaluator Model
        13: 22,  # Response Time
        14: 50,  # Knowledge Base Source
    }

    for column, width in column_widths.items():

        sheet.column_dimensions[
            get_column_letter(column)
        ].width = width

    # Freeze header
    sheet.freeze_panes = "A2"

    # Add filters
    sheet.auto_filter.ref = sheet.dimensions

    # Save
    workbook.save(REPORT_FILE)

    print(
        f"[SUCCESS] Excel report: {REPORT_FILE}"
    )


# ============================================================
# HTML Report
# ============================================================

def generate_html_report(results):

    print("[INFO] Generating HTML report...")

    HTML_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total = len(results)

    passed = sum(
        1
        for result in results
        if get_evaluation_result(result) == "PASS"
    )

    failed = sum(
        1
        for result in results
        if get_evaluation_result(result) == "FAIL"
    )

    unknown = total - passed - failed

    pass_percentage = (
        round(
            (passed / total) * 100,
            2,
        )
        if total
        else 0
    )

    # --------------------------------------------------------
    # Generate rows
    # --------------------------------------------------------

    rows = ""

    for result in results:

        status = get_evaluation_result(
            result
        )

        reason = get_evaluation_reason(
            result
        )

        evaluator_model = get_evaluator_model(
            result
        )

        # ----------------------------------------------------
        # CSS based on result
        # ----------------------------------------------------

        if status == "PASS":
            css_class = "pass"

        elif status == "FAIL":
            css_class = "fail"

        else:
            css_class = "unknown"

        # ----------------------------------------------------
        # Prepare values
        # ----------------------------------------------------

        test_id = display_value(
            result.get("id")
        )

        test_type = display_value(
            result.get("test_type")
        )

        strategy = display_value(
            result.get("strategy")
        )

        category = display_value(
            result.get("category")
        )

        question = display_value(
            result.get("question")
        )

        expected_answer = display_value(
            result.get("expected_answer")
        )

        expected_behavior = display_value(
            result.get("expected_behavior")
        )

        actual_answer = display_value(
            result.get("actual_answer")
        )

        target_model = display_value(
            result.get("target_model")
        )

        evaluator_model = display_value(
            evaluator_model
        )

        response_time = display_value(
            result.get("response_time_seconds")
        )

        source = display_value(
            result.get("source")
        )

        # ----------------------------------------------------
        # HTML row
        # ----------------------------------------------------

        rows += f"""
        <tr>

            <td>{escape(str(test_id))}</td>

            <td>{escape(str(test_type))}</td>

            <td>{escape(str(strategy))}</td>

            <td>{escape(str(category))}</td>

            <td>{escape(str(question))}</td>

            <td>{escape(str(expected_answer))}</td>

            <td>{escape(str(expected_behavior))}</td>

            <td>{escape(str(actual_answer))}</td>

            <td class="{css_class}">
                {escape(str(status))}
            </td>

            <td>{escape(str(reason))}</td>

            <td>{escape(str(target_model))}</td>

            <td>{escape(str(evaluator_model))}</td>

            <td>{escape(str(response_time))}</td>

            <td>{escape(str(source))}</td>

        </tr>
        """

    # --------------------------------------------------------
    # Full HTML
    # --------------------------------------------------------

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>AI Chatbot Automation Report</title>

<style>

body {{
    font-family: Arial, sans-serif;
    margin: 30px;
}}

h1 {{
    margin-bottom: 20px;
}}

.summary {{
    display: flex;
    gap: 20px;
    margin-bottom: 25px;
    flex-wrap: wrap;
}}

.card {{
    border: 1px solid #ccc;
    padding: 15px 25px;
    border-radius: 6px;
    min-width: 90px;
    text-align: center;
}}

.card strong {{
    font-size: 16px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}}

th {{
    background-color: #f2f2f2;
    position: sticky;
    top: 0;
}}

th,
td {{
    border: 1px solid #ddd;
    padding: 10px;
    text-align: left;
    vertical-align: top;
}}

.pass {{
    background-color: #c6efce;
    font-weight: bold;
}}

.fail {{
    background-color: #ffc7ce;
    font-weight: bold;
}}

.unknown {{
    background-color: #ffeb9c;
    font-weight: bold;
}}

</style>

</head>

<body>

<h1>AI Chatbot Automation Report</h1>

<div class="summary">

    <div class="card">
        <strong>Total</strong>
        <br>
        {total}
    </div>

    <div class="card">
        <strong>Passed</strong>
        <br>
        {passed}
    </div>

    <div class="card">
        <strong>Failed</strong>
        <br>
        {failed}
    </div>

    <div class="card">
        <strong>Unknown</strong>
        <br>
        {unknown}
    </div>

    <div class="card">
        <strong>Pass %</strong>
        <br>
        {pass_percentage}%
    </div>

</div>

<table>

<thead>

<tr>

    <th>Test ID</th>

    <th>Test Type</th>

    <th>Strategy</th>

    <th>Category</th>

    <th>Question</th>

    <th>Expected Answer</th>

    <th>Expected Behavior</th>

    <th>Actual Answer</th>

    <th>Result</th>

    <th>Reason</th>

    <th>Target Model</th>

    <th>Evaluator Model</th>

    <th>Response Time</th>

    <th>Knowledge Base Source</th>

</tr>

</thead>

<tbody>

{rows}

</tbody>

</table>

</body>

</html>
"""

    # --------------------------------------------------------
    # Save HTML
    # --------------------------------------------------------

    with open(
        HTML_REPORT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(html)

    print(
        f"[SUCCESS] HTML report: "
        f"{HTML_REPORT_FILE}"
    )


# ============================================================
# Main Report Generator
# ============================================================

def generate_report():

    print(
        "[INFO] Reading evaluated results..."
    )

    results = read_evaluated_results()

    print(
        f"[INFO] Found "
        f"{len(results)} evaluated results."
    )

    generate_excel_report(
        results
    )

    generate_html_report(
        results
    )

    print(
        "[SUCCESS] Report generation completed."
    )

    return results


# ============================================================
# Run Directly
# ============================================================

if __name__ == "__main__":
    generate_report()