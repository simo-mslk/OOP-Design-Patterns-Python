"""Unit tests of ask_groq() with mocks: no key, no network, no tokens.

Mocking rule from the course: mock what you don't own (the Groq API),
test what you own (input validation, the request we build, error propagation).
"""
import os

import pytest

from groq_chat import MAX_TOKENS, MODEL, ask_groq

pytestmark = pytest.mark.unit


def test_ask_groq(fake_groq):
    # Arrange
    client = fake_groq("4")
    # Act
    answer = ask_groq("What is 2+2?", client=client)
    # Assert
    assert answer == "4"


def test_ask_groq_calls_api_correctly(fake_groq):
    client = fake_groq()

    ask_groq("What is 2+2?", client=client)

    client.chat.completions.create.assert_called_once_with(
        model=MODEL,
        messages=[{"role": "user", "content": "What is 2+2?"}],
        max_tokens=MAX_TOKENS,
    )


def test_ask_groq_raises_error_when_api_fails(mocker):
    client = mocker.Mock()
    client.chat.completions.create.side_effect = Exception("API down")

    with pytest.raises(Exception, match="API down"):
        ask_groq("What is 2+2?", client=client)


@pytest.mark.parametrize("blank", ["", " ", "\t\n"])
def test_blank_question_is_refused_before_any_call(fake_groq, blank):
    client = fake_groq()

    with pytest.raises(ValueError, match="empty"):
        ask_groq(blank, client=client)

    client.chat.completions.create.assert_not_called()      # no token burnt


def test_answer_is_returned_as_is(fake_groq):
    long_answer = "Line 1\nLine 2 with émojis 🎉"
    assert ask_groq("hi", client=fake_groq(long_answer)) == long_answer


def test_real_client_is_built_when_none_is_given(mocker, fake_groq):
    # patch Groq where it is USED (groq_chat.Groq), not where it is defined (groq.Groq)
    groq_class = mocker.patch("groq_chat.Groq", return_value=fake_groq("hello"))

    assert ask_groq("hi") == "hello"
    groq_class.assert_called_once_with()


@pytest.mark.live
@pytest.mark.skipif(not os.environ.get("GROQ_API_KEY"), reason="needs a real GROQ_API_KEY")
def test_real_api_smoke():
    """Only run on purpose: pytest -m live (costs a few tokens)."""
    assert ask_groq("Answer with one word: what colour is the sky?").strip()
