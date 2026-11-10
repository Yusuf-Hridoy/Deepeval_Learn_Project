"""
Fixtures for the Zentra chatbot tests. No test functions live here.

    judge.py   - the DeepEval judge model
    client.py  - the HTTP client for the backend
    conftest.py- fixtures only
    test_*.py  - tests only

The backend must be running (start.ps1). From the project root:

    .venv/Scripts/python.exe -m pytest tests/pytest_test -v
"""

import os
import uuid

import pytest
from dotenv import load_dotenv, find_dotenv

from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.metrics.g_eval.utils import Rubric
from deepeval.test_case import LLMTestCaseParams

from client import ZentraClient
from judge import LocalOllamaJudge

load_dotenv(find_dotenv())


# ── CLI options ──────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption("--base-url", default=os.getenv("ZENTRA_BASE_URL", "http://localhost:8000"),
                     help="Zentra backend URL")
    # The judge is deliberately NOT the app's own model: qwen3.5:2b is too small to
    # score Faithfulness/GEval consistently (measured: it fails runs its own reason
    # calls correct). 4b is stable, roughly 2x slower. Override with JUDGE_MODEL.
    parser.addoption("--judge-model", default=os.getenv("JUDGE_MODEL", "qwen3.5:4b"),
                     help="Ollama model used as the DeepEval judge")
    parser.addoption("--judge-url", default=os.getenv("Local_Ollama_Base_Url", "http://localhost:11434"),
                     help="Ollama base URL")
    parser.addoption("--chat-timeout", type=int, default=180,
                     help="Seconds to wait for a chat reply")
    parser.addoption("--threshold", type=float, default=0.5,
                     help="Default pass threshold for metrics")


def pytest_configure(config):
    config.addinivalue_line("markers", "llm: hits the local LLM (slow)")
    config.addinivalue_line("markers", "smoke: fast sanity checks")


# ── Backend ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client(pytestconfig):
    """Shared client; exits immediately with a clear message if the backend is down."""
    c = ZentraClient(
        pytestconfig.getoption("--base-url"),
        chat_timeout=pytestconfig.getoption("--chat-timeout"),
    )
    try:
        c.health()
    except Exception as e:
        pytest.exit(f"Backend not reachable at {c.base_url} ({e}). Run start.ps1 first.", returncode=1)
    yield c
    c.close()


@pytest.fixture
def session_id(client):
    """Fresh chat session per test, wiped afterwards."""
    sid = f"pytest-{uuid.uuid4().hex[:8]}"
    yield sid
    client.reset_session(sid)


# ── Talking to the chatbot ───────────────────────────────────────────────────

@pytest.fixture
def chat(client, session_id):
    """chat("do you sell backpacks?") -> full /api/chat JSON dict."""
    def _chat(message, sid=None):
        return client.chat(message, sid or session_id)

    return _chat


@pytest.fixture
def retrieve(client):
    """retrieve("headphones") -> the product context the metrics score against."""
    def _retrieve(query, k=5):
        return client.retrieval_context(query, k)

    return _retrieve


@pytest.fixture
def cart_product_names(client, session_id):
    """Names currently in this test's cart, read straight from the API."""
    def _names():
        return client.cart_product_names(session_id)

    return _names


# ── Judge + metrics ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def judge(pytestconfig):
    return LocalOllamaJudge(
        pytestconfig.getoption("--judge-model"),
        pytestconfig.getoption("--judge-url"),
    )


@pytest.fixture(scope="session")
def threshold(pytestconfig):
    return pytestconfig.getoption("--threshold")


@pytest.fixture
def answer_relevancy(judge, threshold):
    return AnswerRelevancyMetric(model=judge, threshold=threshold, async_mode=False)


@pytest.fixture
def faithfulness(judge, threshold):
    """Is the reply grounded in the retrieved products, or hallucinated?"""
    return FaithfulnessMetric(model=judge, threshold=threshold, async_mode=False)


@pytest.fixture
def correctness(judge, threshold):
    return GEval(
        name="Correctness",
        model=judge,
        threshold=threshold,
        async_mode=False,
        criteria=(
            "The actual output is correct if it contains the same key facts as the "
            "expected output. Wording, order and grammar differences do not matter. "
            "Do not answer the question yourself, only compare the two texts."
        ),
        # Explicit steps keep a small local judge from inventing its own rules -
        # without them it penalises synonyms and extra detail.
        evaluation_steps=[
            "1. Identify the key facts in the expected output, such as the product name and its price.",
            "2. Check whether those same facts appear in the actual output. Ignore wording, "
            "synonyms, order, formatting and grammar.",
            "3. Extra detail in the actual output (specs, features, follow-up questions) is "
            "acceptable and must NOT lower the score.",
            "4. Score exactly 1.0 if the key facts match, or 0.0 if any of them is missing or contradicted.",
        ],
        # A rubric makes a small judge pick a band instead of inventing a float.
        rubric=[
            Rubric(score_range=(0, 3), expected_outcome="A key fact is missing or contradicted."),
            Rubric(score_range=(4, 6), expected_outcome="The key facts are partly present or ambiguous."),
            Rubric(score_range=(7, 10), expected_outcome="All key facts are present, regardless of wording or extra detail."),
        ],
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    )


@pytest.fixture
def check():
    """check(case, [metric, ...]) - run_async=False so the 2b model isn't hit in parallel."""
    def _check(test_case, metrics):
        assert_test(test_case, metrics, run_async=False)

    return _check
