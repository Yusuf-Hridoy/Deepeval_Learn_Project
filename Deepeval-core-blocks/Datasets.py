import os
from deepeval import test_case
from deepeval import test_case
from dotenv import load_dotenv

load_dotenv()

from deepeval.dataset import EvaluationDataset

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

from langchain_ollama import ChatOllama
llm = ChatOllama(model=MODEL_NAME, base_url=BASE_URL)

test_case_1 = LLMTestCase(
    input="What is the capital of France?",
    expected_output="The capital of France is Paris.",
    actual_output=llm.invoke("What is the capital of France?").content
)

test_case_2 = LLMTestCase(
    input="What is the capital of Germany?",
    expected_output="The capital of Germany is Berlin.",
    actual_output=llm.invoke("What is the capital of Germany?").content
)

dataset = EvaluationDataset()

dataset.add_test_case(test_case_1)
dataset.add_test_case(test_case_2)

dataset.test_cases


evaluate(
    test_cases=dataset.test_cases,
    metrics=[AnswerRelevancyMetric(model=judge, verbose_mode=True)],
    async_config=AsyncConfig(run_async=False),
)