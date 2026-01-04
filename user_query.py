import dspy
from extract import ExtractUnits, ConversionValidator, AskFormula, FormulaTestCaseGenerator, ExtractedUnits, FormulaResult
from neo import lookup_conversion, store_conversion, ConversionRelation
from test_runner import run_formula_tests, failed_test_cases_to_markdown, TestRunnerOutput
from utils import console

#The pipeline
class KGAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.extract_units = ExtractUnits()
        self.conversion_validator = ConversionValidator()
        self.ask_formula = AskFormula()
        self.test_case_generator = FormulaTestCaseGenerator()

    def forward(self, question: str) -> str:
        # STEP 1: Extract units
        units: ExtractedUnits= self.extract_units(question)  #An ExtractedUnits pydantic instance is returned

        # STEP 2: Check the knowledge graph
        formula: str | None = lookup_conversion(units)  #Returns formula string or None

        #If formula is found in the KG, return it
        if formula:
            return f"Formula found in the knowledge graph: {formula}"
        
        #Initialize the loop count and feedback string
        loop_counter: int = 0
        feedback: str = ""

        #Conversion Validator checks if the unit conversion is possible
        is_valid: bool = self.conversion_validator(units)

        if not is_valid:
            console.print("Conversion is not possible")
            return None # Conversion is not Possible so it will return None 

        #Conversion is valid, proceed to ask the LLM for formula and test it
        #While Loop Starts from here
        while(loop_counter < 3):  #Limit to 3 iterations for safety
            # STEP 3: If formula is missing (lookup_conversion gives None) → Ask LLM for the formula
            console.print("Loop Counter = ", loop_counter)

            result: FormulaResult = self.ask_formula(units=units,feedback=feedback)  # returns a FormulaResult instance
            
            console.print(f"LLM provided formula: {result.formula}")

            #Test the "Ask Formula" Agents output by Generating Test Cases 
            
            test_cases = self.test_case_generator(result.formula)  #Returns a TestCaseSet instance which is already validated beforehand
            console.print(f"Generated Test Cases: {test_cases.test_cases}")

            #The test runner will return a score based on how many test cases passed

            test_runner_output: TestRunnerOutput = run_formula_tests(
                formula = result.formula,
                test_cases = test_cases.test_cases
            )
            console.print(f"Formula Test Score: {test_runner_output.score}")
            console.print(f"Failed Test Cases: {test_runner_output.failed_test_cases}")

            #If the score is above a certain threshold, the formula is stored in the KG (At least 8 cases have to pass) and the loop breaks
            if(test_runner_output.score >= 0.8):
                data = ConversionRelation.model_validate(
                {
                        "from_unit":units.from_unit,
                        "to_unit": units.to_unit,
                        "formula": result.formula,
                        "author": "Reevan"
                    }
                )
                store_conversion(data)
                return f"I learned this rule from the LLM: {result.formula}"

            #Else, the feedback score is sent back to the AskFormula module for fine-tuning 
            markdown_feedback: str = failed_test_cases_to_markdown(test_runner_output.failed_test_cases, result.formula)

            #More detailed feedback which allows for modification
            feedback: str = f"""
            ## 🔍 Formula Evaluation Feedback

            **Formula:**
            {result.formula}

            **Test Results:**  
            Passed **{10 - len(test_runner_output.failed_test_cases)} / 10** test cases.

            {markdown_feedback}

            ### 🔧 Required Action
            Please correct the formula so that it passes **all** test cases.
            """.strip()

            loop_counter: int = loop_counter + 1 #Increment loop counter after checking the score


        console.print(f"Unable to determine a reliable formula after {loop_counter} attempts.")
        return None


agent = KGAgent()


