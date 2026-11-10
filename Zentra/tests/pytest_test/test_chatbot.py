"""
Zentra shopping assistant - test cases.

Judge, metrics and the chat client are set up in conftest.py, so each test
only writes its own LLMTestCase and runs it.
"""

import pytest

from deepeval.test_case import LLMTestCase


# ── Smoke: no LLM judging ────────────────────────────────────────────────────

@pytest.mark.smoke
def test_backend_is_healthy(client):
    assert client.health()["status"] == "healthy"


@pytest.mark.smoke
def test_chat_returns_a_reply(chat):
    reply = chat("hi")
    assert reply["response"].strip(), "assistant returned an empty reply"
    assert "products_mentioned" in reply


# ── Case 1: the reply must answer what was asked ─────────────────────────────

@pytest.mark.llm
def test_product_question_is_relevant(chat, retrieve, answer_relevancy, check):
    question = "what headphones do you have?"

    test_case_1 = LLMTestCase(
        input=question,
        actual_output=chat(question)["response"],
        retrieval_context=retrieve(question),
    )

    check(test_case_1, [answer_relevancy])


# ── Case 2: every claim must come from the catalogue ─────────────────────────

@pytest.mark.llm
def test_product_question_is_grounded(chat, retrieve, faithfulness, check):
    question = "tell me about the Volta Wireless Bluetooth Headphones"

    test_case_2 = LLMTestCase(
        input=question,
        actual_output=chat(question)["response"],
        retrieval_context=retrieve(question),
    )

    check(test_case_2, [faithfulness])


# ── Case 3: catalogue fact - the Volta headphones are $79.99 ─────────────────

@pytest.mark.llm
def test_price_answer_is_correct(chat, retrieve, correctness, check):
    question = "how much are the Volta Wireless Bluetooth Headphones?"

    test_case_3 = LLMTestCase(
        input=question,
        actual_output=chat(question)["response"],
        expected_output="The Volta Wireless Bluetooth Headphones cost $79.99.",
        retrieval_context=retrieve(question),
    )

    check(test_case_3, [correctness])


# ── Case 4: a vague need still gets a real, catalogue-backed suggestion ──────

@pytest.mark.llm
def test_recommendation_is_relevant_and_grounded(chat, retrieve, answer_relevancy, faithfulness, check):
    question = "I need something to carry my laptop to work"

    test_case_4 = LLMTestCase(
        input=question,
        actual_output=chat(question)["response"],
        retrieval_context=retrieve(question),
    )

    check(test_case_4, [answer_relevancy, faithfulness])


# ── Case 5: the assistant's action, not its words ────────────────────────────

@pytest.mark.llm
def test_add_to_cart_actually_updates_the_cart(chat, cart_product_names):
    reply = chat("add the Haverly Laptop Backpack to my cart")
    assert reply["cart_updated"] is True, f"cart was not updated: {reply['response']}"

    names = cart_product_names()
    assert any("Backpack" in n for n in names), f"backpack missing from cart: {names}"
