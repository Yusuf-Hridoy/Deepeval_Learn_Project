"""DeepEval judge model. Not collected by pytest (no test_ prefix)."""

import ollama
from deepeval.models import DeepEvalBaseLLM


class LocalOllamaJudge(DeepEvalBaseLLM):
    """Local judge. think=False keeps qwen3.5 out of reasoning mode (otherwise 30-100s/call)."""

    def __init__(self, model_name, base_url, keep_alive=300):
        self.model_name = model_name
        self.keep_alive = int(keep_alive)   # Ollama needs integer seconds here
        self.client = ollama.Client(host=base_url)

    def load_model(self):
        return self.client

    def generate(self, prompt, schema=None):
        response = self.client.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            think=False,
            keep_alive=self.keep_alive,
            format=schema.model_json_schema() if schema else None,
        )
        text = response.message.content
        return schema.model_validate_json(text) if schema else text

    async def a_generate(self, prompt, schema=None):
        return self.generate(prompt, schema)

    def get_model_name(self):
        return self.model_name
