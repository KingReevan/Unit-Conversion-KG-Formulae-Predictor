import math
from typing import List
from engine import parse_formula, evaluate_formula
from extract import TestCase

def run_formula_tests(
    formula: str,
    test_cases: List[TestCase],
    *,
    rel_tol: float = 1e-9,
    abs_tol: float = 1e-12,
) -> float:
    """
    Runs test cases against a unit conversion formula.

    Returns:
        A score between 0.0 and 1.0 indicating the fraction of passing tests.
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

        except Exception:
            # Any evaluation failure counts as test failure
            continue

    return passed / len(test_cases)
