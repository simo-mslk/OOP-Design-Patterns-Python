# 06 - Testing & mocking

Statement: slide 93 + the "Mocking" part of https://courses.dallard.tech/ci_cd/testing_python_intro/

| File | What it is |
|---|---|
| [`groq_chat.py`](groq_chat.py) | `ask_groq()` from the course |
| [`test_groq_chat.py`](test_groq_chat.py) | **unit** tests with `mocker`: the 3 tests of the course (fake answer, check the exact request, API down) + blank questions, patching the default client, and one `live` test |
| [`chat_api.py`](chat_api.py) | the FastAPI + Groq app of slide 93, made testable |
| [`test_chat_api.py`](test_chat_api.py) | **integration** tests with FastAPI's `TestClient`: `/status`, `/chat`, invalid bodies, and every Groq error mapped to an HTTP code |
| [`conftest.py`](conftest.py) | shared fixtures: `fake_groq(answer)` factory, fake HTTP request, Groq HTTP errors |

```bash
pip install -r ../requirements.txt
python3 -m pytest                # everything, no API key needed (the live test is excluded)
python3 -m pytest -m unit        # only the unit tests
python3 -m pytest -m integration # only the API tests
python3 -m pytest --cov=.        # coverage (95% on this folder)
GROQ_API_KEY=... python3 -m pytest -m live   # the only test that calls the real API
```

## Why mock?

Calling the real Groq API in tests means: an API key on every machine (and the risk of pushing it), internet access, tokens paid at each run, slow tests, random failures when Groq is down, and an answer that changes every time so it can't be compared with `==`.

A mock is a fake object with the same shape: `client.chat.completions.create(...)` returns something where `.choices[0].message.content` is whatever I decide. Then I test **my** code: that it refuses a blank question without calling the API, that it sends the right model / messages / max_tokens, that it lets an API error go up, and that the app turns each error into the right HTTP code. Checking that the LLM answers well is Groq's job, not my tests'.

> Mocking rule: mock what you don't own (the API), test what you own.

## How the code is made testable

- `ask_groq(question, client=None)`: the client is a parameter (**dependency injection**), so a test passes a mock. When no client is given, the real `Groq()` is created; to test that path I patch `groq_chat.Groq`, i.e. where it is **used**, not `groq.Groq`.
- `chat_api.create_app(client_factory)`: in the slide the Groq client is created when the module is imported, and the Groq SDK refuses to create a client without an API key, so even importing the app in a test fails. With an app factory, production uses the real client and the tests give `lambda: mock`. The client is created lazily, so `/status` works even without a key.
- The model of the slide (`mixtral-8x7b-32768`) was removed by Groq → `llama-3.3-70b-versatile`.

## Error mapping tested

| Groq exception | HTTP answer |
|---|---|
| `APITimeoutError` | 504 "API Timeout" (checked first: it is a subclass of `APIConnectionError`) |
| `APIConnectionError` | 500 "API Connection Error" |
| `RateLimitError` | 429 "Rate Limit Exceeded" (checked before `APIStatusError`, its parent) |
| other `APIStatusError` (401, 503...) | same status code, "API Status Error" |
| invalid / blank body | 422, and Groq is never called |

## Other notions of the course used here

- **Fixtures + conftest.py**: setup shared by both test files, no copy-paste.
- **Markers**: `unit`, `integration`, `live` are declared in `pyproject.toml` and selected with `-m`.
- **Parametrize**: one test function, many cases (blank strings, error types).
- **Arrange / Act / Assert**: visible in `test_ask_groq` and in the other tests' structure.
- **Coverage**: `pytest --cov` shows that only the real client creation and the `__main__` blocks are not covered.
