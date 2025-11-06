# Testing Guide

This guide explains how to set up and run tests for the Library Management System, including backend unit tests, integration tests, basic UI checks, and accessibility reviews.

## Prerequisites

- Python 3.10+
- A virtual environment activated
- Project dependencies installed

```bash
pip install -r requirements.txt
```

Recommended developer tools (install if you plan to run tests locally):

```bash
pip install pytest pytest-cov pytest-mock
```

Optional tools:

```bash
# Linting / formatting
pip install flake8 black isort

# Type checking
pip install mypy

# Accessibility and UI checks (external/manual)
# Lighthouse (Chrome devtools), axe DevTools (browser extension)
```

## Configuration for Tests

- The app uses an application factory. Tests should create an app with a testing configuration.
- Use an in-memory SQLite database for isolation.

Example PyTest fixture (conftest.py):

```python
import os
import tempfile
import pytest
from app import create_app
from app.extensions import db  # if you have a central db instance

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SERVER_NAME': 'localhost',
        'PRESERVE_CONTEXT_ON_EXCEPTION': False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
```

Adjust imports to your project structure as needed.

## Running Tests

- Run all tests:

```bash
pytest -q
```

- Run with coverage report:

```bash
pytest --cov=app --cov-report=term-missing
```

- Run a specific test file or test:

```bash
pytest tests/test_auth.py::test_login_success -q
```

## Test Structure

Recommended layout:

```
project/
├── app/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_catalog.py
│   ├── test_circulation.py
│   ├── test_errors.py
│   └── test_reports.py
└── TESTING.md
```

## What to Test

- Authentication
  - Register: valid/invalid data, duplicate username/email
  - Login/Logout: success/failure, remember me
  - Access control: protected routes redirect when unauthenticated; 403 for insufficient roles

- Catalog
  - CRUD operations for books/categories
  - Form validation: required fields, constraints
  - Search and pagination behavior

- Circulation
  - Borrow/Return flows
  - Overdue logic and fines (if applicable)
  - Status transitions and constraints

- Reports
  - Routes respond with 200 for valid users/roles
  - Date range filtering behavior
  - CSV/PDF export endpoints return correct content types

- Errors & UX
  - Custom error handlers: 400, 401, 403, 404, 429, 500
  - Error templates render expected messages

## Sample Tests

```python
# tests/test_errors.py

def test_404(client):
    res = client.get('/non-existent')
    assert res.status_code == 404
    assert b"Not Found" in res.data or b"404" in res.data

# tests/test_auth.py

def test_login_page_loads(client):
    res = client.get('/auth/login')
    assert res.status_code == 200
    assert b"Sign In" in res.data
```

## Linting and Formatting

- Run formatters:

```bash
black app tests
isort app tests
```

- Run linter:

```bash
flake8 app tests
```

## Type Checking (optional)

```bash
mypy app
```

## Accessibility and UX Checks (manual)

- Keyboard navigation
  - All interactive elements reachable with Tab/Shift+Tab
  - Visible focus indicator on focusable controls
  - Escape closes modals

- Screen reader and ARIA
  - Landmarks present: header, nav, main, footer
  - ARIA roles/labels on alerts, modals, form errors
  - Live regions announce flash messages

- Color and contrast
  - Meets WCAG 2.1 AA contrast (use Lighthouse or axe)

- Reduced motion
  - No blocking/large animations when `prefers-reduced-motion` is set

- Responsive behavior
  - Pages usable on small screens; no horizontal scrolling

Use Lighthouse (Chrome DevTools > Lighthouse) and axe DevTools extension to audit pages including error pages and forms.

## UI Smoke Tests (optional)

For lightweight browser checks, you can use `pytest` with `selenium` or `playwright`.

Example (Playwright):

```bash
pip install pytest-playwright
playwright install chromium
```

```python
# tests/test_ui_smoke.py

def test_homepage_has_title(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:5000/')
    assert "Library" in page.title() or page.locator('h1,h2').first.is_visible()
    browser.close()
```

Run the dev server in another terminal (`flask run` or `python run.py`) before UI tests.

## Continuous Integration (CI) (optional)

- Configure your CI to run: install deps, run tests with coverage, and lint.
- Cache pip and Playwright browsers (if used) for faster builds.

---

If you need example test files scaffolded, let me know and I’ll add a minimal `tests/` suite to get you started.
