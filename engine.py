from sympy import symbols, sympify, Eq, solve
import re

#Regex pattern to match variable names with spaces so that they can be replaced with underscores
VARIABLE_PATTERN = re.compile(
    r'\b([a-zA-Z]+(?:\s+[a-zA-Z]+)+)\b'
)

def normalize_variables(formula: str) -> str:
    """
    Replaces spaces within multi-word variable names with underscores.

    Args:
        formula: The string containing variables with spaces (e.g., "total price").

    Returns:
        A string where "variable name" becomes "variable_name".
    """
    def replacer(match):
        return match.group(1).replace(" ", "_")

    return VARIABLE_PATTERN.sub(replacer, formula)


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

    lhs = symbols(lhs_str)  #Converts the LHS into a sympy symbol
    rhs_str: str = rhs_str.replace('×','*').replace("÷", "/")   
    rhs_expr = sympify(rhs_str)  #Converts RHS into a sympy expression

    return lhs_str, lhs, rhs_expr


def evaluate_formula(formula: str, **inputs) -> float:        #Takes in a formula string and variable inputs
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

    formula = normalize_variables(formula)
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

    #Add Test Case Generation and Test Runner before returning the inverse formula. 
    return inverse_formula


