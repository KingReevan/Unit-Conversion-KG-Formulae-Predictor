from extract import ExtractUnits, ask_formula
from generate_questions import genq
from mass_edge_storage import save_all_conversions
from timing import timeit

extractor = ExtractUnits()  # instantiate the unit extractor

@timeit
def training_loop(cycles: int, questions_per_cycle: int) -> None:
    """
    Runs the unit conversion training pipeline.

    Steps:
    1. Generate unit conversion questions
    2. Extract source and target units
    3. Generate conversion formulas
    4. Store conversions in the graph
    """

    print(f"Starting training for {cycles} cycles...\n")

    for i in range(cycles):
        print(f"--- Cycle {i+1} ---")

        # STEP 1: Ask the LLM to give me questions of unit conversions -> "how do I convert centimeter to meter?"
        generated_questions = genq(
            count = questions_per_cycle,
            prompt = "Give me strings of unit conversion questions. The units must be simple and commonly used."
        )
        print(generated_questions.questions)

        # STEP 2: Extract units from the generated questions
        unit_pairs = {}

        for key, q in generated_questions.questions.items():
            result = extractor(q)

            unit_pairs[key] = {
                "from_unit": result.from_unit,
                "to_unit": result.to_unit
            }

        print(unit_pairs)

        # STEP 3: Generate formulas for the extracted units
        formulas = {}   # store results here
        for key, pair in unit_pairs.items():
            from_unit = pair["from_unit"]
            to_unit = pair["to_unit"]

            result = ask_formula(from_unit=from_unit, to_unit=to_unit)

            # result.formula is the clean string
            formulas[key] = {
                "from_unit": from_unit,
                "to_unit": to_unit,
                "formula": result.formula
            }

        print(formulas)

        # STEP 4: Save all Nodes and edges in the graph
        save_all_conversions(formulas)

    print("Training complete.")
