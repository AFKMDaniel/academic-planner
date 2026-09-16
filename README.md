# Academic Planner

A small desktop application for planning academic work.

## Structure

```
app/
├── main.py          # application entry point
├── database/        # database connection and session setup
├── models/          # SQLAlchemy models
├── services/        # business logic
└── ui/              # PySide6 windows and widgets

tests/               # automated tests
resources/           # icons, images and other static assets
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python -m app.main
```

## Test

```bash
pytest
```
