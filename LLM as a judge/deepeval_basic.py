import os
from dotenv import load_dotenv

load_dotenv()

import ollama
from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase

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

test_case = LLMTestCase(
    input="What is the capital of France?",
    actual_output="Paris.",
    expected_output="The capital of France is Paris.",
)

evaluate(
    test_cases=[test_case],
    metrics=[AnswerRelevancyMetric(model=judge, verbose_mode=True)],
    async_config=AsyncConfig(run_async=False),
)