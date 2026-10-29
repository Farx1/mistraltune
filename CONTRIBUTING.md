# Contributing to MistralTune

Thank you for your interest in contributing to MistralTune! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/Farx1/mistraltune.git
   cd mistraltune
   ```

2. **Set up the development environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   
   # Install dependencies (API + tests; add requirements-train.txt for local QLoRA)
   pip install -r requirements-api.txt
   pre-commit install  # optional: runs ruff on commit
   
   # Install frontend dependencies
   cd frontend
   npm install
   cd ..
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your MISTRAL_API_KEY (optional for testing)
   ```

## Code Standards

### Python

- **Linting**: We use [Ruff](https://github.com/astral-sh/ruff) for linting
  ```bash
  ruff check src/ tests/
  ```

- **Formatting**: not enforced by CI yet. Use `ruff format` on the files you touch.

- **Type hints**: Prefer type hints for function parameters and return values
- **Docstrings**: Use Google-style docstrings for public functions

### TypeScript/React

- **Linting**: We use ESLint with Next.js configuration
  ```bash
  cd frontend
   npm run lint
   ```

- **Formatting**: Use Prettier (if configured) or follow ESLint rules

## Testing

### Running Tests

All tests run in **DEMO_MODE** by default (mocked API):

```bash
# Run all tests (what CI runs)
DEMO_MODE=1 pytest -m "not slow"

# Slow tests (train a tiny model on CPU, needs requirements-train.txt)
pytest -m slow

# Run specific test file
pytest tests/test_api_endpoints.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

- **Test files**: Must follow `test_*.py` naming convention
- **Test functions**: Must start with `test_`
- **Fixtures**: Use `conftest.py` for shared fixtures
- **Mocking**: Use `DEMO_MODE=1` or `pytest-mock` for API mocking
- **No GPU/downloads**: Tests should not require GPU or download large models

### Test Coverage

Aim for:
- All API endpoints have at least one test
- Critical business logic is covered
- Edge cases are tested

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation if needed

3. **Run checks locally**
   ```bash
   # Backend
   ruff check src/ tests/
   pytest tests/ -v
   
   # Frontend
   cd frontend
   npm run lint
   npm run build
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```
   
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for code refactoring
   - `chore:` for maintenance

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then create a Pull Request on GitHub.

6. **CI Checks**
   - All CI checks must pass
   - At least one review is required
   - Address any review comments

## Project Structure

```
mistraltune/
├── src/              # Backend source code
│   ├── api/         # FastAPI application
│   └── utils/       # Utility functions
├── frontend/        # Next.js frontend
├── tests/           # Test suite
├── configs/         # Configuration files
├── data/            # Datasets and data files
└── scripts/         # Utility scripts
```

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Be respectful and constructive in discussions

Thank you for contributing! 🚀

