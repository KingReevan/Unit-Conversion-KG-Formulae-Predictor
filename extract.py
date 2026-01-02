import dspy
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
from typing import Optional

load_dotenv()

dspy.configure(
    lm=dspy.LM(
        model="openai/gpt-4o-mini",
    )
)

#Pydantics Models
class ExtractedUnits(BaseModel):
    from_unit: str
    to_unit: str

class FormulaResult(BaseModel):
    formula: str

#Signature to extract and validate conversion units, returns pydantic
class ExtractUnits(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.extract = dspy.Predict("question -> from_unit, to_unit")

    def forward(self, question: str) -> ExtractedUnits:
        raw_units = self.extract(question=question)
        cleaned_units = ExtractedUnits.model_validate(raw_units.toDict())
        return cleaned_units

class AskFormula(dspy.Module):

    class FormulaSignature(dspy.Signature):
        """
        Task: Generate a mathematical formula for converting one unit into another.

        Rules:
        1. Always use FULL unit names (e.g., "meters per second", never "m/s").
        2. Never abbreviate unit names.
        3. Use only:
        - '*' for multiplication
        - '/' for division
        - '**' for exponentiation
        4. Minimize the number of mathematical operations.
        5. The equation MUST be in the form:
        to_unit = <expression involving from_unit>
        6. The left-hand side (LHS) must always be the to_unit.
        """

        from_unit: str = dspy.InputField(
            desc="The full unit name to convert FROM. Never abbreviated."
        )
        to_unit: str = dspy.InputField(
            desc="The full unit name to convert TO. Never abbreviated."
        )
        feedback: str = dspy.InputField(
            desc=(
                "Feedback from failed test cases. "
                "the expected behavior, and what must be corrected. "
                "Use this feedback to avoid repeating the same mistake."
            ),
            default=""
        )

        formula: str = dspy.OutputField(
            desc="The conversion formula using full unit names only. No abbreviations.",
            type=str
        )

    def __init__(self) -> None:
        super().__init__()
        self.predict = dspy.Predict(self.FormulaSignature)

    def forward(self, units: ExtractedUnits) -> FormulaResult:
        """
        Docstring for forward
        
        :param self: The AskFormula Instance
        :param from_unit: The unit to be converted from
        :param to_unit: The unit to be converted to
        """

        raw = self.predict(from_unit=units.from_unit, to_unit=units.to_unit)
        print(raw)

        # Validate output after LLM prediction
        validated = FormulaResult.model_validate(raw.toDict())
        return validated

ask_formula = AskFormula()


