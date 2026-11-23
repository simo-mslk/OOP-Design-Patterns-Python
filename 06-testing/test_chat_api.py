"""Integration tests of the FastAPI app: real HTTP layer (TestClient), fake Groq client."""
import groq
import pytest
from fastapi.testclient import TestClient

from chat_api import MODEL, SYSTEM_PROMPT, create_app

pytestmark = pytest.mark.integration


@pytest.fixture
def groq_mock(fake_groq):
    return fake_groq("Paris")


@pytest.fixture
def api(groq_mock):
    """A fresh app whose Groq client is the mock."""
    return TestClient(create_app(client_factory=lambda: groq_mock))


def test_status(api):
    response = api.get("/status")
    assert response.status_code == 200
    assert response.json() == {"message": "OK"}


def test_chat_returns_the_model_answer(api, groq_mock):
    response = api.post("/chat", json={"prompt": "Capital of France?"})

    assert response.status_code == 200
    assert response.json() == {"response": "Paris"}
    sent = groq_mock.chat.completions.create.call_args.kwargs
    assert sent["model"] == MODEL
    assert sent["messages"] == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Capital of France?"},
    ]


def test_client_is_created_once_for_all_requests(groq_mock, mocker):
    factory = mocker.Mock(return_value=groq_mock)
    api = TestClient(create_app(client_factory=factory))
    for _ in range(3):
        api.post("/chat", json={"prompt": "hi"})
    factory.assert_called_once()
    assert groq_mock.chat.completions.create.call_count == 3


def test_status_never_needs_the_client(mocker):
    factory = mocker.Mock(side_effect=RuntimeError("no API key"))
    api = TestClient(create_app(client_factory=factory))
    assert api.get("/status").status_code == 200
    factory.assert_not_called()


@pytest.mark.parametrize("body", [{}, {"question": "wrong field"}, {"prompt": ""}, {"prompt": "   "}])
def test_invalid_bodies_get_422_and_never_reach_groq(api, groq_mock, body):
    assert api.post("/chat", json=body).status_code == 422
    groq_mock.chat.completions.create.assert_not_called()


def test_connection_error_gives_500(api, groq_mock, groq_request):
    groq_mock.chat.completions.create.side_effect = groq.APIConnectionError(request=groq_request)
    response = api.post("/chat", json={"prompt": "hi"})
    assert (response.status_code, response.json()) == (500, {"detail": "API Connection Error"})


def test_timeout_gives_504(api, groq_mock, groq_request):
    groq_mock.chat.completions.create.side_effect = groq.APITimeoutError(request=groq_request)
    response = api.post("/chat", json={"prompt": "hi"})
    assert (response.status_code, response.json()) == (504, {"detail": "API Timeout"})


@pytest.mark.parametrize("error_class, status, detail", [
    (groq.RateLimitError, 429, "Rate Limit Exceeded"),
    (groq.AuthenticationError, 401, "API Status Error"),
    (groq.InternalServerError, 503, "API Status Error"),
])
def test_status_errors_keep_their_code(api, groq_mock, groq_http_error, error_class, status, detail):
    groq_mock.chat.completions.create.side_effect = groq_http_error(error_class, status)
    response = api.post("/chat", json={"prompt": "hi"})
    assert response.status_code == status
    assert response.json() == {"detail": detail}


def test_module_imports_without_api_key(monkeypatch):
    """The slide version crashed at import without a key; this one doesn't."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    import importlib

    import chat_api
    assert importlib.reload(chat_api).app is not None
