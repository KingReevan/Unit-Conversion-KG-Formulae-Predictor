import dspy
from extract import ExtractUnits, ask_formula, test_case_generator
from neo import lookup_conversion, store_conversion, ConversionRelation

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
        
        # STEP 3: If formula is missing (lookup_conversion gives None) → Ask LLM for the formula
        result = ask_formula(units)  # returns a FormulaResult instance
        if(result is None):
            return "The conversion between these units is not meaningful."
        
        print(f"LLM provided formula: {result.formula}")

        #Test the Ask Formula output by Generating Test Cases 
        
        test_cases = test_case_generator(result.formula)  #Returns a TestCaseSet instance which is already validated beforehand
        print(f"Generated Test Cases: {test_cases.test_cases}")
        
        # and Running those test cases in a test runner
        #The test runner will return a score based on how many test cases passed
        #If the score is agbove a certain threshold, the formula is stored in the KG
        #Else, the feedback score is sent back to the AskFormula module for fine-tuning (A loop is created here)

        # STEP 4: Store it in the knowledge graph
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


agent = KGAgent()


