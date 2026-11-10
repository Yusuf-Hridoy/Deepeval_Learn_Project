import os
from dotenv import load_dotenv

from deepeval.test_case import LLMTestCase
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.models import GeminiModel

load_dotenv()

gemini = GeminiModel(
    model="gemini-3.5-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("Google_Api_Key"),
)

test_case = LLMTestCase(
    input="What is the capital of France?",
    expected_output="The capital of France is Paris.",
    actual_output="Paris."
)

evaluate([test_case], metrics=[
    AnswerRelevancyMetric(model=gemini)
])
