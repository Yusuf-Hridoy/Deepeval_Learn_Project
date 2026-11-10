import os
import json
from dotenv import load_dotenv
from deepeval.test_case import LLMTestCase

load_dotenv()

from deepeval.dataset import EvaluationDataset, Golden
from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.models import DeepEvalBaseLLM

import ollama
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

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
llm = ChatOllama(model=MODEL_NAME, base_url=BASE_URL)

MAX_SAMPLES = 5  # limit how many goldens to evaluate (dev.json is huge, ~57k lines)

dev_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev.json")  # resolve dev.json next to this script
with open(dev_json_path, "r", encoding="utf-8") as f:
    squad_data = json.load(f)

dataset = EvaluationDataset()

# Convert SQuAD Q&A pairs into DeepEval goldens
for article in squad_data["data"]:
    for paragraph in article["paragraphs"]:
        for qa in paragraph["qas"]:
            golden = Golden(
                input=qa["question"],
                expected_output=qa["answers"][0]["text"],
                context=[paragraph["context"]],
            )
            dataset.add_golden(golden)
            if len(dataset.goldens) >= MAX_SAMPLES:
                break
        if len(dataset.goldens) >= MAX_SAMPLES:
            break
    if len(dataset.goldens) >= MAX_SAMPLES:
        break

"""
dataset.goldens

evaluate(
    goldens=dataset.goldens,
    metrics=[AnswerRelevancyMetric(model=judge, verbose_mode=True)],
    async_config=AsyncConfig(run_async=False),
)
"""
print(f"loaded {len(dataset.goldens)} goldens from SQuAD dev.json")
dataset.goldens[0]

# convert golden in test case 

for golden in dataset.goldens[:10]:  # limit to first 10 for demonstration

    

    test_case = LLMTestCase(
        input=golden.input,
        expected_output=golden.expected_output,
        context=golden.context,
        actual_output=llm.invoke(f"Context: {golden.context[0]}\n\nQuestion: {golden.input}").content  # context goes inside the prompt
    )

    dataset.add_test_case(test_case)

dataset.test_cases

evaluate(
    test_cases=dataset.test_cases,
    metrics=[AnswerRelevancyMetric(model=judge, verbose_mode=True)],
    async_config=AsyncConfig(run_async=False),
)


