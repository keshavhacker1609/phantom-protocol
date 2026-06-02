# Contributing to Phantom Protocol

Thank you for your interest in contributing. This document covers how to set up
the development environment, the code standards we follow, and how to submit changes.

---

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/phantom-protocol.git
cd phantom-protocol

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Frontend
cd ../frontend
npm install
```

Run tests:
```bash
cd backend
python -m pytest tests/ -v
```

---

## Code Standards

- **Python**: type hints on all public functions, no bare `except Exception`
- **Async**: all I/O must be async — never block the event loop
- **Logging**: use `get_logger(__name__)`, include context in every log line
- **Error responses**: always return `{"error": "...", "message": "...", "request_id": "..."}`
- **No hardcoded data**: all responses must come from DB, Redis, or live computation

---

## Pull Request Process

1. Fork and create a feature branch: `git checkout -b feature/your-feature`
2. Make changes with clear, focused commits
3. Verify all Python files pass syntax: `python -m py_compile backend/**/*.py`
4. Open a PR with a clear description of what changed and why

---

## Reporting Issues

Open an issue with:
- Python version and OS
- Full error traceback
- Steps to reproduce
- Expected vs actual behavior
