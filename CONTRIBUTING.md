# Contributing to Phantom Protocol

Contributions are welcome — bug fixes, new attack pattern signatures, frontend improvements, documentation, or new mesh network features.

---

## Development Setup

```bash
git clone https://github.com/keshavhacker1609/phantom-protocol.git
cd phantom-protocol

# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Frontend
cd ../frontend
npm install
```

---

## Code Standards

- **Python** — type hints on all public functions, `async` for all I/O
- **No bare `except Exception`** — always catch specific exceptions or re-raise
- **Logging** — use `get_logger(__name__)`, include context (session_id, node_id)
- **Error responses** — always return `{"error": "...", "message": "...", "request_id": "..."}`
- **No hardcoded data** — all responses from DB, Redis, or live computation

---

## Pull Request Process

1. Fork the repo and create a feature branch: `git checkout -b feature/your-feature`
2. Make changes with focused, well-described commits
3. Verify Python syntax: `python -m py_compile backend/**/*.py`
4. Test the attack simulator still works: `python demo/attack_simulator.py --scenario 1`
5. Open a PR with a clear description of what changed and why

---

## Good First Issues

- Add new attack patterns to `backend/modules/sentinel/patterns.py`
- Improve fake data variety in `backend/modules/deception/response_generator.py`
- Add new D3.js visualization to the dashboard
- Write tests for the detection engine

---

## Reporting Issues

Open an issue with:
- Python version and OS
- Full error traceback
- Steps to reproduce
- Expected vs actual behavior
