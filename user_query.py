import dspy
from extract import ExtractUnits, ask_formula, test_case_generator
from neo import lookup_conversion, store_conversion, ConversionRelation
from test_runner import run_formula_tests, failed_test_cases_to_markdown
from extract import ExtractedUnits, TestCase

#The pipeline
class KGAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.extract_units = ExtractUnits()

    def forward(self, question: str) -> str:
        # STEP 1: Extract units
        units = self.extract_units(question)  #An ExtractedUnits pydantic instance is returned

        # STEP 2: Check the knowledge graph
        formula = lookup_conversion(units)  #Returns formula string or None

        #If formula is found in the KG, return it
        if formula:
            print("Formula found in Knowledge Graph")
            return f"From the knowledge graph: {formula}"
        
        #Initialize the loop count and feedback string
        loop_counter: int = 0
        feedback: str = ""

        #While Loop Starts from here
        while(loop_counter < 3):  #Limit to 3 iterations for safety
            # STEP 3: If formula is missing (lookup_conversion gives None) → Ask LLM for the formula
            print("Loop Counter = ", loop_counter)

            result = ask_formula(units=units,feedback=feedback)  # returns a FormulaResult instance
            if(result is None):
                return "The conversion between these units is not meaningful."
            
            print(f"LLM provided formula: {result.formula}")

            #Test the "Ask Formula" Agents output by Generating Test Cases 
            
            test_cases = test_case_generator(result.formula)  #Returns a TestCaseSet instance which is already validated beforehand
            print(f"Generated Test Cases: {test_cases.test_cases}")

            #The test runner will return a score based on how many test cases passed
            score, failed_cases  = run_formula_tests(
                formula = result.formula,
                test_cases = test_cases.test_cases
            )
            print(f"Formula Test Score: {score}")
            print(f"Failed Test Cases: {failed_cases}")

            #If the score is above a certain threshold, the formula is stored in the KG (At least 8 cases have to pass) and the loop breaks
            if(score >= 0.8):
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
            
            loop_counter: int = loop_counter + 1 #Increment loop counter after checking the score

            #Else, the feedback score is sent back to the AskFormula module for fine-tuning 
            markdown_feedback: str = failed_test_cases_to_markdown(failed_cases, result.formula)

            feedback: str = f"""
            ## 🔍 Formula Evaluation Feedback

            **Formula:**
            {result.formula}

            **Test Results:**  
            Passed **{10 - len(failed_cases)} / 10** test cases.

            {markdown_feedback}

            ### 🔧 Required Action
            Please correct the formula so that it passes **all** test cases.
            """.strip()

        return f"Unable to determine a reliable formula after multiple attempts."


agent = KGAgent()


