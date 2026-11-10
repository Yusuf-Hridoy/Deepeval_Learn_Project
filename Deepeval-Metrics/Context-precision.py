import os
from dotenv import load_dotenv

load_dotenv()

import ollama
from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import AnswerRelevancyMetric, GEval, ContextualPrecisionMetric
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

MODEL_NAME = os.getenv("Local_Ollama_Model")
BASE_URL = os.getenv("Local_Ollama_Base_Url")


class LocalOllamaJudge(DeepEvalBaseLLM):
    def __init__(self, model_name, base_url):
        self.model_name = model_name
        self.client = ollama.Client(host=base_url)

    def load_model(self):
        return self.client

    def generate(self, prompt, schema=None):
        response = self.client.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            think=False,
            format=schema.model_json_schema() if schema else None,
        )
        text = response.message.content
        return schema.model_validate_json(text) if schema else text

    async def a_generate(self, prompt, schema=None):
        return self.generate(prompt, schema)

    def get_model_name(self):
        return self.model_name


judge = LocalOllamaJudge(MODEL_NAME, BASE_URL)

# Case 1: exact match -> should PASS
test_case_1 = LLMTestCase(
    input="What is the capital of France?",
    actual_output="The capital of France is Paris.",
    expected_output="The capital of France is Paris.",
)

# Case 2: same fact, different word order -> should PASS (tests robustness)
test_case_2 = LLMTestCase(
    input="What is the capital of Germany?",
    actual_output="Berlin is the capital of Germany.",
    expected_output="The capital of Germany is Berlin.",
)

# Replace this with the actual output from your LLM application
actual_output = "We offer a 30-day full refund at no extra cost."
# Replace this with the expected output of your RAG generator
expected_output = "You are eligible for a 30 day full refund at no extra cost."
# Replace this with the actual retrieved context from your RAG pipeline
retrieval_context = ["All customers are eligible for a 30 day full refund at no extra cost."]
metric = ContextualPrecisionMetric(
    threshold=0.7,
    model=judge,
    include_reason=True
)
test_case = LLMTestCase(
    input="What if these shoes don't fit?",
    actual_output=actual_output,
    expected_output=expected_output,
    retrieval_context=retrieval_context
)
# To run metric as a standalone

evaluate(test_cases=[test_case], metrics=[metric], async_config= AsyncConfig(run_async= False))