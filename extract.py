import dspy
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
from typing import Optional
from utils import console

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

class TestCase(BaseModel):
    input_value: float
    expected_output: float

class TestCaseSet(BaseModel):
    test_cases: list[TestCase]

    @field_validator("test_cases")
    @classmethod
    def must_have_exactly_10(cls, v):
        if len(v) != 10:
            raise ValueError("Exactly 10 test cases are required")
        return v


#Signature to extract and clean conversion units, returns pydantic
class ExtractUnits(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.extract = dspy.Predict("question -> from_unit, to_unit")

    def forward(self, question: str) -> ExtractedUnits:
        raw_units = self.extract(question=question)
        cleaned_units = ExtractedUnits.model_validate(raw_units.toDict())
        return cleaned_units


class ConversionValidator(dspy.Module):
    class ConversionValiditySignature(dspy.Signature):
        """
        Task: Determine whether converting from one unit to another is possible.

        A conversion is VALID if:
        - The conversion is conceptually meaningful and conversion is possible.

        A conversion is INVALID if:
        - Units are unrelated concepts (e.g., animals, objects, abstract nouns).

        Examples:
        - "teaspoons" → "tablespoons" → VALID
        - "meters" → "kilometers" → VALID
        - "seconds" → "centuries" → VALID

        - "teaspoons" → "centuries" → INVALID
        - "sheep" → "goats" → INVALID
        - "meters" → "seconds" → INVALID
        """

        from_unit: str = dspy.InputField(
            desc="The full unit name to convert FROM."
        )
        to_unit: str = dspy.InputField(
            desc="The full unit name to convert TO."
        )

        valid: bool = dspy.OutputField(
            desc="True if the conversion is meaningful, otherwise False."
        )

    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict(self.ConversionValiditySignature)

    def forward(self, units: ExtractedUnits) -> bool:
        result = self.predict(
            from_unit=units.from_unit,
            to_unit=units.to_unit
        )
        return result.valid


class FormulaTestCaseGenerator(dspy.Module):

    class FormulaTestCaseSignature(dspy.Signature):
        """
        Task: Generate exactly 10 numerical test cases for a unit conversion formula.

        The formula represents a deterministic mathematical relationship.

        Rules:
        - Each test case must include:
            - input_value (float)
            - expected_output (float)
        - Try to Cover:
            - baseline value
            - standard value
            - fractional value
            - zero
            - decimal input
            - very small input
            - high precision input
            - negative value
            - large value
            - edge case relevant to the formula

        Constraints:
        - Generate EXACTLY 10 test cases.
        - Ensure high precision for 'expected_output'.
        - If the unit represents a physical quantity that cannot be negative (e.g., length, mass), do not generate negative inputs.
        - Return raw floats, no units strings.
        """

        formula: str = dspy.InputField(
            desc="A unit conversion formula, e.g. 'centimeters = meters * 100'"
        )

        test_cases: list[TestCase] = dspy.OutputField(
            desc="Exactly 10 test cases derived from the formula"
        )

    def __init__(self):
        super().__init__()
        # ChainOfThought is used to allow the model to "think" about the math
        self.generate = dspy.ChainOfThought(self.FormulaTestCaseSignature)

    def forward(self, formula: str) -> TestCaseSet:
        console.print("Using Chain of Thought for Test Case Generation")
        prediction = self.generate(formula=formula)

        # Convert DSPy output → Pydantic
        validated = TestCaseSet.model_validate(
            {"test_cases": prediction.test_cases}
        )

        return validated


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
        7. If the spelling for units have british and american variations, use british spelling.
        8. Unit names must be in plural form (e.g., "meters", "inches").
        """

        from_unit: str = dspy.InputField(
            desc="The full unit name to convert FROM. Never abbreviated."
        )
        to_unit: str = dspy.InputField(
            desc="The full unit name to convert TO. Never abbreviated."
        )
        feedback: str = dspy.InputField(
            desc=(
                "Feedback from failed test cases describing incorrect formulas, "
                "expected behavior, and required corrections. "
                "Use this to avoid repeating past mistakes."
            ),
            default=""
        )

        formula: str = dspy.OutputField(
            desc="The correct conversion formula using full unit names only. No abbreviations.",
            type=str
        )
    

    def __init__(self) -> None:
        super().__init__()
        self.validator = ConversionValidator()
        self.predict = dspy.Predict(self.FormulaSignature) #The Formula Signature is passed here

    def forward(self, units: ExtractedUnits, feedback: str = "") -> FormulaResult:
        """
        Docstring for forward
        
        :param self: The AskFormula Instance
        :param from_unit: The unit to be converted from
        :param to_unit: The unit to be converted to
        :param feedback: Feedback from previous test case failures to improve formula accuracy
        """
        
        raw_predicted_formula = self.predict(from_unit=units.from_unit, to_unit=units.to_unit, feedback=feedback) #Prediction is performed here

        # Validate output after LLM prediction
        validated = FormulaResult.model_validate(raw_predicted_formula.toDict())
        return validated
