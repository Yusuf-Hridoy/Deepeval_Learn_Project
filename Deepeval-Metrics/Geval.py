import os
from dotenv import load_dotenv

load_dotenv()

import ollama
from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import AnswerRelevancyMetric, GEval
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

# Case 3: wrong fact -> should FAIL
test_case_3 = LLMTestCase(
    input="What is the capital of Japan?",
    actual_output="The capital of Japan is Kyoto.",
    expected_output="The capital of Japan is Tokyo.",
)


# this for the Geval 
correctness = GEval(
    name = "Correctness",
    model=judge,
    criteria=(
        "The actual output is correct if it contains the SAME key facts as the "
        "expected output. Word order, capitalization and grammar differences do not matter. "
        "Do NOT answer the question, only compare the two texts."
    ),
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    evaluation_steps=[
        "1. Find the main fact in the expected output (e.g. the capital city and the country).",
        "2. Check if that same fact also appears in the actual output.",
        "3. If the fact matches, the score must be 1.0. If it contradicts or is missing, the score must be 0.0. Write the score exactly as 1.0 or 0.0.",
    ],

)




evaluate(
    test_cases=[test_case_1, test_case_2, test_case_3],
    metrics=[correctness],
    async_config=AsyncConfig(run_async=False),
)