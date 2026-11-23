"""FastAPI + Groq chat API (slide 93), reorganized so it can be tested without the real API.

What I changed compared to the slide:
- the slide creates the Groq client at import time with the API key, so just importing
  the module (e.g. in a test) needs a key. Here the app is built by create_app(), which
  receives a *factory* for the client: production passes the real Groq client, the tests
  pass a function that returns a mock.
- the Groq model of the slide (mixtral-8x7b-32768) has been removed by Groq, I use
  llama-3.3-70b-versatile.
- a timeout gets its own 504 answer (it is checked before the generic connection error,
  because APITimeoutError is a subclass of APIConnectionError), and an empty prompt is
  refused with 422 before calling the API.
"""
import logging
import os
from typing import Callable, Optional

import groq
from fastapi import Depends, FastAPI, HTTPException
from groq import Groq
from pydantic import BaseModel, Field

MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = "You are a helpful assistant."

logger = logging.getLogger("chat_api")


class Prompt(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    response: str


def make_groq_client() -> Groq:
    """Real client, only created when the first request arrives."""
    return Groq(api_key=os.environ.get("GROQ_API_KEY"), timeout=20.0, max_retries=1)


def create_app(client_factory: Callable[[], Groq] = make_groq_client) -> FastAPI:
    app = FastAPI(title="Groq chat API")
    cache: dict = {}

    def get_client() -> Groq:
        # one client for the whole app, created lazily
        if "client" not in cache:
            cache["client"] = client_factory()
        return cache["client"]

    @app.get("/status")
    async def get_status():
        return {"message": "OK"}

    @app.post("/chat", response_model=ChatResponse)
    async def post_chat(prompt: Prompt, client: Groq = Depends(get_client)):
        if not prompt.prompt.strip():
            raise HTTPException(status_code=422, detail="Prompt cannot be blank")
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt.prompt},
                ],
            )
        except groq.APITimeoutError:
            logger.warning("Groq did not answer in time")
            raise HTTPException(status_code=504, detail="API Timeout")
        except groq.APIConnectionError as error:
            logger.error("The server could not be reached: %s", error.__cause__)
            raise HTTPException(status_code=500, detail="API Connection Error")
        except groq.RateLimitError:
            logger.warning("429 received from Groq, we should back off")
            raise HTTPException(status_code=429, detail="Rate Limit Exceeded")
        except groq.APIStatusError as error:
            logger.error("Groq answered %s", error.status_code)
            raise HTTPException(status_code=error.status_code, detail="API Status Error")
        return ChatResponse(response=completion.choices[0].message.content)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)
