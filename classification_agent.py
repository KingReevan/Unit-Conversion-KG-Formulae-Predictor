import dspy
from dotenv import load_dotenv
import json
from typing import Dict, List
from pydantic import BaseModel
from utils import console

load_dotenv()

dspy.configure(
    lm=dspy.LM(
        model="openai/gpt-4o-mini",
    )
)

class ParagraphClassificationOutput(BaseModel):
    category: List[str]
    reasoning: str

class ParagraphClassificationSignature(dspy.Signature):
    """
    You are a classification agent.

    You will be given:
    1. A paragraph of text
    2. A JSON object describing classification categories and their definitions

    Your task:
    - Carefully analyze each sentence in the paragraph to inform your classification
    - Determine which category or categories best match the paragraph
    - Base your decision strictly on the provided category definitions
    - Do not invent categories
    - Do not modify category names
    - You may select multiple categories if applicable
    - If no categories match, respond with "None"
    - If the JSON object is empty, respond with "Categories not provided"
    - If the JSON object has a lot of categories, focus on the most relevant ones
    
    Output Requirements:
    - Return one or more category names exactly as provided
    - Provide a short justification for each selected category
    """

    paragraph: str = dspy.InputField(desc="Paragraph to be classified")

    category_definitions: str = dspy.InputField(
        desc="JSON mapping of category name to category definition"
    )

    selected_categories: List[str] = dspy.OutputField(
        desc="List of category names that best match the paragraph. If categories do not match, return ['None']. If no categories provided, return ['Categories not provided']"
    )

    reasoning: str = dspy.OutputField(
        desc="Brief explanation justifying why these categories were selected"
    )

 
# 2. Define the classification agent
class ParagraphClassifier(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classify = dspy.Predict(ParagraphClassificationSignature)
 
    def forward(self, paragraph: str, category_definitions: str) -> ParagraphClassificationOutput:
        # Inject category constraints into the prompt
 
        prediction = self.classify(
            paragraph=paragraph,
            category_definitions=category_definitions
        )

        return prediction
 
json_category_definitions = {
    "Technical": "Paragraphs that discuss technical topics, concepts, or jargon related to specific fields such as engineering, computer science, or technology.",
    "Marketing": "Paragraphs that focus on promoting products, services, or brands, often using persuasive language and highlighting benefits to potential customers.",
    "Legal": "Paragraphs that contain legal terminology, discuss laws, regulations, contracts, or legal procedures.",
    "Financial": "Paragraphs that deal with financial topics such as investments, markets, economic trends, personal finance, or accounting.",
    "Health": "Paragraphs that cover topics related to health, medicine, wellness, medical conditions, treatments, or healthcare systems.",
    "Manufacturer": "Information that identifies who makes or produces the product. Includes manufacturer name, brand, OEM/ODM details, parent company, or manufacturing responsibility.",
    "Address": "Information describing physical or legal locations. Includes manufacturer address, headquarters, production site, mailing address, city, country, or place of origin."
}

# # 3. Example usage
if __name__ == "__main__":
 
    classifier = ParagraphClassifier()
 
    sample_paragraph = """
    Various calibration options are available for the configurable
    output signals of the KiTorq System. The calibration takes
    place on a high-precision calibration system that is traceable
    to ­national standards.
 
        Eulachstrasse 22, 8408 Winterthur, Switzerland
    phone +41 52 224 11 11, Fax +41 52 224 14 14, info@kistler.com, www.kistler.com
    Kistler is a registered trademark of Kistler Holding AG."""
 
    while True:
        input_paragraph: str = input("Enter the paragraph to classify: ")

        result = classifier(input_paragraph,json.dumps(json_category_definitions))
    
        console.print("Selected Categories: ", result.selected_categories)
        console.print("Reasoning: ", result.reasoning)


