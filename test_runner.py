import math
from typing import List
from pydantic import BaseModel, field_validator
from engine import parse_formula, evaluate_formula, normalize_variables
from extract import TestCase
from utils import console

class TestRunnerOutput(BaseModel):
    score: float
    failed_test_cases: List[TestCase]
    actual_outputs_for_failed_test_cases: List[float]

def run_formula_tests(
    formula: str,
    test_cases: List[TestCase],
    *,
    rel_tol: float = 0.0,   # Adjust these parameters for the floating point comparison
    abs_tol: float = 1e-3,   # Values are allowed to be different only after 3 decimal places
) -> TestRunnerOutput:
    """
    Runs test cases against a unit conversion formula.

    Returns:
        (score, failed_test_cases)
        - score: float between 0.0 and 1.0
        - failed_test_cases: list of TestCase objects that failed
    """

    formula = normalize_variables(formula)
    console.print("Normalized formula in test runner: ", formula)
    
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
    actual_outputs_for_failed_test_cases = []

    for case in test_cases:
        try:
            output = evaluate_formula(
                formula,
                **{input_var: case.input_value}
            ) #The formula is evaluated here, input is the formula string and the test case input value
            if math.isclose(     #Compares the expected output and actual
                output,
                case.expected_output,
                rel_tol=rel_tol,
                abs_tol=abs_tol,
            ):
                passed += 1
            else:
                failed_cases.append(case)
                actual_outputs_for_failed_test_cases.append(output)

        except Exception:
            # Any evaluation failure counts as test failure
            failed_cases.append(case)

    test_score: float = passed / len(test_cases)

    output = TestRunnerOutput(
        score=test_score,
        failed_test_cases=failed_cases,
        actual_outputs_for_failed_test_cases=actual_outputs_for_failed_test_cases
    )

    return output

def failed_test_cases_to_markdown(
    failed_cases: List[TestCase],
    formula: str | None = None
) -> str:
    
    """
    Creates a markdown table summarizing failed test cases. Returns an empty string if there are no failed cases.
    """

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

#This formula does not work for reasons unexplained
# formula = "kelvin = (fahrenheit - 32) * (5/9) + 273.15"

# test_cases = [
#     TestCase(input_value=0, expected_output=-459.67),
#     TestCase(input_value=2.5, expected_output=2950.0),
# ]

# score, failures = run_formula_tests(formula, test_cases)
# print("Test Results: ", formula)
# print(score)  # 1.0 if all pass
# print(failures)  # [] if all pass

