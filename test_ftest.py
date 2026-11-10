from deepeval.test_case import LLMTestCase
from deepeval import evaluate;
from deepeval.metrics import ExactMatchMetric

test_case = LLMTestCase(
    input="What is the capital of France?",
    expected_output="The capital of France is Paris.",
    actual_output="The capital of France is Paris."
)

evaluate ([test_case], metrics=[
    ExactMatchMetric()
])