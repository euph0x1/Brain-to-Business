# Brain-to-Business

An AI agent that turns random thoughts, everyday problems and creative ideas into a practical
startup brief: a clarified idea, real competitors (via web search), target customers, revenue
models, a scored evaluation, and a week-by-week MVP roadmap.

Runs on the **free Gemini API tier** (no credit card). Competitor research uses free DuckDuckGo
search (no key).

## Quick start (VS Code)

1. Install Python 3.11+ and the VS Code **Python** extension. Open this folder in VS Code.
2. Open the terminal (Ctrl+`) and run:

   ```bash
   python -m venv venv
   # Windows:  venv\Scripts\activate        Mac/Linux:  source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Get a free key at <https://aistudio.google.com> (Get API key).
4. Copy `.env.example` to `.env` and paste your key. If the default `MODEL` errors, copy a
   current Flash model ID from the AI Studio model list into `.env`.
5. Run it:

   ```bash
   streamlit run app.py                 # web UI
   python main.py "students overpay for textbooks"   # command line
   ```
   You can also press F5 in VS Code and pick a configuration from the dropdown.

## How it works

```
raw thought
   -> 1 Clarify   (you confirm or correct it)
   -> 2 Research  (web search -> competitors + gaps)
   -> 3 Customers (segments, pain level, where to find them)
   -> 4 Revenue   (2-3 models with pricing logic)
   -> 5 Evaluate  (6 criteria scored 1-10, verdict, risks)
   -> 6 Roadmap   (no-code validation test first, then weekly plan)
   -> Markdown report + saved to SQLite
```
Every step returns a validated Pydantic object, and each step sees what earlier steps found.
The evaluator is prompted to be critical, not a cheerleader.

## CLI commands

| Command | What it does |
|---|---|
| `python main.py "idea"` | Analyze an idea (asks you to confirm first) |
| `python main.py` | Same, but prompts for the idea |
| `--yes` | Skip the confirmation step |
| `--no-search` | Skip web search |
| `--list` | List saved ideas |
| `--show 3` | Print saved idea #3 |
| `--compare 1 3` | Score table comparing two ideas |
| `--refine 3 "target students in India"` | Re-run with a change, saved as a new idea |

Reports are also written to `reports/idea-<id>.md`. Ideas live in `ideas.db` (SQLite).

## Project layout

```
app.py              Streamlit UI (analyze, history, refine, compare, download)
main.py             CLI
b2b/config.py       settings from .env
b2b/llm.py          Gemini wrapper: structured output, retries, friendly errors
b2b/schemas.py      Pydantic models for every step
b2b/prompts.py      one prompt per step
b2b/tools.py        web search tool
b2b/pipeline.py     clarify / research / analyze / refine
b2b/storage.py      SQLite history
b2b/report.py       Markdown rendering + comparison
tests/              pytest suite (uses a fake model: no key needed)
```

## Troubleshooting

- **404 / model not found**: change `MODEL` in `.env` to a current ID from AI Studio.
- **429 / rate limited**: the free tier is limited per minute. The app retries automatically;
  raise `CALL_DELAY` in `.env` (e.g. 5) if it keeps happening.
- **"No live search results"**: DuckDuckGo may have rate-limited you. Results fall back to the
  model's own knowledge and the report says so. Verify competitors yourself in that case.
- **Privacy**: free-tier Gemini inputs may be used by Google to improve its models. Don't paste
  confidential information.
- Run the tests with `pytest` (no API key needed).

## Ideas to extend it

Export to PDF, a "pitch deck outline" step, a market-size estimator, auto-generated interview
questions for the validation step, or switching providers by editing only `b2b/llm.py`.
