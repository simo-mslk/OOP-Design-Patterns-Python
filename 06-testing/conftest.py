"""Fixtures shared by test_groq_chat.py and test_chat_api.py."""
import httpx
import pytest

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


@pytest.fixture
def fake_groq(mocker):
    """Factory fixture: fake_groq("some answer") returns a mock with the same shape as Groq.

    client.chat.completions.create(...) returns an object where
    .choices[0].message.content == answer
    """
    def build(answer: str = "4"):
        choice = mocker.Mock()
        choice.message.content = answer
        client = mocker.Mock()
        client.chat.completions.create.return_value = mocker.Mock(choices=[choice])
        return client
    return build


@pytest.fixture
def groq_request():
    """Fake HTTP request, needed to build the Groq exceptions."""
    return httpx.Request("POST", GROQ_URL)


@pytest.fixture
def groq_http_error(groq_request):
    """groq_http_error(cls, 503) builds an APIStatusError subclass with that status code."""
    def build(error_class, status: int):
        response = httpx.Response(status, request=groq_request)
        return error_class(f"HTTP {status}", response=response, body=None)
    return build
