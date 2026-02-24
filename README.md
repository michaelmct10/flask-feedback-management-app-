# Flask Feedback Management App

A full-stack Flask web application for managing feedback entries through a web UI and REST-style API endpoints.

## Features
- Create, view, edit and delete feedback (CRUD)
- Dashboard with filtering + sorting
- Pagination for large datasets
- JSON API endpoints (search / summaries / bulk actions)
- Bulk upload endpoint (JSON payload)
- Automated tests using pytest

## Tech Stack
- Python + Flask
- SQLAlchemy (ORM)
- SQLite
- Jinja2 templates + Bootstrap
- pytest

## Project Structure
- `app.py` — app entry point
- `feedback/` — blueprint (routes + models)
- `templates/` — HTML templates
- `static/` — JS/CSS/images
- `tests.py` — automated tests

## Run locally (basic)

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask flask_sqlalchemy flask_bootstrap pytest
python3 app.py
```

Open: `http://127.0.0.1:5000/feedback`
