# Story Thread Tracker

Story Thread Tracker is a local-first AI manuscript memory and continuity tool
for long-form writers.

The app lets writers upload or sync a manuscript, organize it by chapter, build
a local searchable story memory, ask questions, and inspect the exact supporting
passages behind each answer.

## What It Does

- Upload `.txt` and `.docx` manuscripts
- Detect English and Chinese chapter headings
- Split long chapters into searchable passages
- Build a multilingual semantic-search index locally
- Save multiple story projects under `user_data/`
- Answer factual and open-ended questions when an OpenAI API key is configured
- Show exact supporting chapter passages
- Browse the full manuscript by chapter
- Keep private manuscripts, indexes, and API keys out of GitHub

Without an API key, the app still performs local search and shows the best
matching passages. With an API key, it also writes a natural-language answer
from the retrieved evidence.

## Project Structure

```text
story-thread-tracker/
├── app.py
├── manuscript_parser.py
├── retriever.py
├── qa.py
├── storage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── sample_data/
│   └── sample_story.txt
└── tests/
    └── test_parser.py
```

## Run Locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the app:

```bash
streamlit run app.py
```

The first launch may take longer because the local multilingual embedding model
needs to be downloaded.

## Test With Sample Data

Upload:

```text
sample_data/sample_story.txt
```

Then click **Build story memory** and ask:

```text
Which chapter mentions the ancient god?
```

The app should retrieve Chapter 3 as the strongest supporting evidence.

## Enable AI Answers

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and replace:

```text
OPENAI_API_KEY=your_api_key_here
```

with your real OpenAI API key.

The default model is:

```text
OPENAI_MODEL=gpt-5.4-mini
```

You can change it later in `.env`.

ChatGPT subscriptions and OpenAI API billing are separate. A ChatGPT Plus
subscription does not include API usage.

## Privacy Behavior

The code is public, but story data remains local. These are ignored by Git:

```text
user_data/
.env
*.docx
*.doc
*.db
```

When AI answering is enabled, the app sends only:

```text
the writer's question
+
the retrieved manuscript passages
```

It does not send the entire manuscript for every question.

## Run Tests

```bash
pytest
```
