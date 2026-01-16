# Contributing to Silent Factory

Thank you for your interest in contributing to Silent Factory! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Redis server (Docker recommended)
- Google Gemini API key

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/BourguignonSimon/projectAI.git
   cd projectAI
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Code Style

We use the following tools to maintain code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking

### Running Code Quality Checks

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8

# Type check
mypy *.py
```

### Pre-commit Hooks

Pre-commit hooks run automatically on each commit. To run manually:

```bash
pre-commit run --all-files
```

## Development Workflow

### Branching Strategy

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

3. Push and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Messages

Follow conventional commit format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add context compression for large conversations
fix: resolve Redis connection timeout issue
docs: update README with installation instructions
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_utils.py
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Name test functions with `test_` prefix

Example:
```python
# tests/test_utils.py
import pytest
from utils import get_next_sequence

def test_get_next_sequence_increments():
    # Test implementation
    pass
```

## Architecture Guidelines

### Agent Communication

All agents communicate through Redis Streams. When adding new agents:

1. Define the agent's role and responsibilities
2. Implement using `agent_generic.py` pattern
3. Add configuration in `.env` if needed
4. Update `start_wsl.sh` to include the new agent

### Message Format

Messages must include:
- `request_id` - Unique project identifier
- `sequence_id` - Ordering within project
- `sender` - Agent name
- `content` - Message payload
- `type` - Message type
- `status` - Processing status

## Pull Request Guidelines

1. **Title**: Use conventional commit format
2. **Description**: Explain what and why
3. **Tests**: Add tests for new functionality
4. **Documentation**: Update relevant docs
5. **Review**: Address reviewer feedback promptly

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No sensitive data in commits

## Reporting Issues

When reporting issues, include:

1. Python version
2. Operating system
3. Steps to reproduce
4. Expected behavior
5. Actual behavior
6. Relevant logs

## Questions?

If you have questions, please open an issue with the `question` label.

## License

By contributing, you agree that your contributions will be licensed under the same terms as the project.
