# OOP & Design Patterns in Python - exercises

My solutions to the exercises of the **OOP & Design Patterns in Python** course. Course website: https://courses.dallard.tech/

| # | Folder | Topic | Slide |
|---|---|---|---|
| 1 | [`01-git`](01-git) | Git mini exercise (all 11 parts + reflection questions) and `install.sh` | 26 |
| 2 | [`02-bash`](02-bash) | Bash automation script `env_install.sh` (6 features + all bonus) | 18 |
| 3 | [`03-oop`](03-oop) | Operator overloading and inheritance problems | 67 |
| 4 | [`04-uml`](04-uml) | UML in Mermaid: hospital system and ABCD Records, + Python implementation | 68 |
| 5 | [`05-design-patterns`](05-design-patterns) | Factory, Builder, Singleton, Adapter, Decorator, Strategy, Template Method | 70-87 |
| 6 | [`06-testing`](06-testing) | Unit and integration tests with mocks (Groq API, FastAPI) | 93 |

Each folder has its own README with the link to the statement, my answers to the questions and how to run the code.

## Run everything

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest                       # 115 tests, no API key needed
python3 -m pytest 05-design-patterns    # one folder only
```

The pytest configuration (test folders and markers) is in [`pyproject.toml`](pyproject.toml). The Groq key, if you want to try the real API, goes in the `GROQ_API_KEY` environment variable, never in the repository (`.env` is in `.gitignore`).

## How I worked

One branch per exercise (`exo/01-git`, `exo/02-bash`, ...), merged into `main` with `--no-ff` when the exercise was finished, so each exercise is visible as a block in the history:

```bash
git log --oneline --graph
```
