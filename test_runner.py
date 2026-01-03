import math
from typing import List
from pydantic import BaseModel, field_validator
from engine import parse_formula, evaluate_formula
from extract import TestCase

class TestRunnerOutput(BaseModel):
    score: float
    failed_test_cases: List[TestCase]

def run_formula_tests(
    formula: str,
    test_cases: List[TestCase],
    *,
    rel_tol: float = 1e-9,
    abs_tol: float = 1e-12,
) -> TestRunnerOutput:
    """
    Runs test cases against a unit conversion formula.

    Returns:
        (score, failed_test_cases)
        - score: float between 0.0 and 1.0
        - failed_test_cases: list of TestCase objects that failed
    """

    # Parse formula once
    lhs_str, lhs, rhs_expr = parse_formula(formula)

    # Extract RHS variable name(s)
    rhs_vars = list(rhs_expr.free_symbols)

    if len(rhs_vars) != 1:
        raise ValueError(
            f"Formula must have exactly one input variable, got {rhs_vars}"
        )

    input_var = rhs_vars[0].name

    passed = 0
    failed_cases: List[TestCase] = []

    for case in test_cases:
        try:
            output = evaluate_formula(
                formula,
                **{input_var: case.input_value}
            )

            if math.isclose(
                output,
                case.expected_output,
                rel_tol=rel_tol,
                abs_tol=abs_tol,
            ):
                passed += 1
            else:
                failed_cases.append(case)

        except Exception:
            # Any evaluation failure counts as test failure
            failed_cases.append(case)


    test_score = passed / len(test_cases)
    output = TestRunnerOutput(
        score=test_score,
        failed_test_cases=failed_cases
    )
    
    return output

def failed_test_cases_to_markdown(
    failed_cases: List[TestCase],
    formula: str | None = None
) -> str:
    if not failed_cases:
        return ""

    lines = []

    lines.append("### ❌ Failed Test Cases\n")

    if formula:
        lines.append(f"The formula `{formula}` failed the following tests:\n")
    else:
        lines.append("The generated formula failed the following tests:\n")

    lines.append("| # | Input Value | Expected Output |")
    lines.append("|---|-------------|-----------------|")

    for idx, case in enumerate(failed_cases, start=1):
        lines.append(
            f"| {idx} | {case.input_value} | {case.expected_output} |"
        )

    lines.append("\nPlease correct the formula so that **all tests pass**.")

    return "\n".join(lines)


# formula = "centimeters = meters * 100"

# test_cases = [
#     TestCase(input_value=1.0, expected_output=100.0),
#     TestCase(input_value=2.5, expected_output=2950.0),
#     TestCase(input_value=0.0, expected_output=40.0),
#     TestCase(input_value=-1.0, expected_output=-100.0),
# ]

# score, failures = run_formula_tests(formula, test_cases)
# print(score)  # 1.0 if all pass
# print(failures)  # [] if all pass

# markdown_report = failed_test_cases_to_markdown(failures, formula)
# print(markdown_report)  # Markdown report of failed test cases