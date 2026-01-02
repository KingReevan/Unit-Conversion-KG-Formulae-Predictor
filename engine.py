from sympy import symbols, sympify, Eq, solve


def parse_formula(formula: str):
    """
    Parses a formula like:
        "meters = centimeters / 100"
    Returns:
        lhs_var, rhs_expr (as SymPy objects)
    """
    lhs_str, rhs_str = formula.split("=")
    lhs_str: str = lhs_str.strip()
    rhs_str = rhs_str.strip()

    lhs = symbols(lhs_str)

    rhs_str: str = rhs_str.replace('×','*').replace("÷", "/")
    rhs_expr = sympify(rhs_str)

    return lhs_str, lhs, rhs_expr #I will make a pydantic for this later


def evaluate_formula(formula: str, **inputs) -> float:
    """
    Evaluates formulas stored in KG safely.
    
    Example:
       evaluate_formula("meters = centimeters / 100", centimeters=250)
       → returns 2.5
    """

    lhs_str, lhs, rhs_expr = parse_formula(formula)
    
    # Convert variables into sympy symbols
    subs = {}
    for var, value in inputs.items():
        subs[symbols(var)] = value

    result = rhs_expr.subs(subs)

    return float(result)


def invert_formula(formula: str) -> str:
    """
    Takes a formula like:
        meters = centimeters / 100
    Returns the inverted formula string:
        centimeters = meters * 100
    """

    u1_str, u1_sym, expr = parse_formula(formula)

    # The RHS should contain exactly one variable (the input unit)
    vars_in_rhs = list(expr.free_symbols)

    if len(vars_in_rhs) != 1:
        raise ValueError(f"Formula must contain exactly one RHS variable. Got: {vars_in_rhs}")
    
    u2_sym = vars_in_rhs[0]
    u2_str = str(u2_sym)

    # Solve u1 = expr for u2
    solution = solve(Eq(u1_sym, expr), u2_sym)

    if not solution:
        raise ValueError("Unable to invert formula")

    inverse_expr = solution[0]
    inverse_formula = f"{u2_str} = {inverse_expr}"

    return inverse_formula

