import os
from dotenv import load_dotenv, find_dotenv
from deepeval.evaluate import AsyncConfig
from deepeval.models import OllamaModel

from deepeval.test_case import LLMTestCase
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.models import GeminiModel

load_dotenv(find_dotenv())

ollama_model = OllamaModel(
      model="qwen3.5:2b",
      base_url="http://localhost:11434"
  )


test_case = LLMTestCase(
    input="What is the capital of France?",
    expected_output="The capital of France is Paris.",
    actual_output="Paris."
)

evaluate(test_cases=[test_case], 
         metrics=[AnswerRelevancyMetric(model=ollama_model)],
async_config=AsyncConfig(run_async=False)
)
