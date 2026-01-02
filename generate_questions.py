import dspy
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

dspy.configure(
    lm=dspy.LM(
        model="openai/gpt-4o-mini",
        temperature=0.8, 
        top_p=0.95
    )
)

# -----------------------------
# OUTPUT DATA MODEL
# -----------------------------
class GeneratedQuestions(BaseModel):
    questions: dict


# -----------------------------
# DSPY SIGNATURE
# -----------------------------
class QuestionSignature(dspy.Signature):
    """
    Task: Create natural-language unit conversion questions.
    IMPORTANT:
    - Each question MUST ask about converting one unit into another.
    - Use full words, NEVER abbreviations (e.g., 'meters', not 'm').
    - Questions must be simple: 'How do I convert X to Y?'
    - Output MUST be valid JSON.
    """

    instruction: str = dspy.InputField()
    count: int = dspy.InputField()

    json_output: str = dspy.OutputField(
        desc="A JSON object with keys like 'question_1', 'question_2', ... and string values."
    )


# -----------------------------
# DSPY MODULE
# -----------------------------
class GenerateQuestions(dspy.Module):

    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict(QuestionSignature)

    def forward(self, count: int, prompt: str) -> GeneratedQuestions:
        """
        :param count: Number of questions to generate
        :param prompt: Optional custom prompt to guide the LLM
        """

        if prompt is None:
            prompt = (
                "Generate natural-language questions asking how to convert one unit to another. "
                "Use full unit names, no abbreviations. "
                "Return only JSON."
            )

        raw = self.predict(instruction=prompt, count=count)

        # Parse JSON string returned by LLM
        try:
            import json
            data = json.loads(raw.json_output)
        except Exception as e:
            raise ValueError(f"LLM returned invalid JSON: {raw.json_output}") from e

        return GeneratedQuestions(questions=data)


genq = GenerateQuestions()

#--------------------------------------------------------------------------------------------------------
import asyncio

async def genq_async(count: int, prompt: str) -> GeneratedQuestions:
    return await asyncio.to_thread(genq.forward, count, prompt)
