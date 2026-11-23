"""ask_groq() - the function used in the "Mocking" part of the course.

Calling it for real needs GROQ_API_KEY, internet and tokens; the tests never do that,
they give it a fake client instead (dependency injection through the `client` argument).
"""
from typing import Optional

from groq import Groq

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 1024


def ask_groq(question: str, client: Optional[Groq] = None) -> str:
    """Send a question to Groq and return the answer."""
    if not question.strip():
        raise ValueError("Question cannot be empty")

    client = client or Groq()          # the real client reads GROQ_API_KEY from the environment
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": question}],
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import os

    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit("export GROQ_API_KEY=... first (never write the key in the code)")
    print(ask_groq("In one sentence, what is a mock in unit testing?"))
