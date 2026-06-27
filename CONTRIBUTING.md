# Contributing to Lithic

Thank you for your interest in contributing to Lithic! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and inclusive.

## How to Contribute

### Reporting Issues

- Check if the issue already exists in [GitHub Issues](https://github.com/DelwarOfficial/Lithic/issues)
- Provide a clear description of the problem
- Include steps to reproduce, expected behavior, and actual behavior
- Add your OS version, Python version, and relevant logs

### Feature Requests

- Describe the feature and its use case
- Explain how it fits into Lithic's goals (graph-first, compression, concise responses)
- Provide examples of how it would be used

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
4. **Run tests**
   ```bash
   pytest tests/ -q
   ```
5. **Submit a pull request**
   - Provide a clear description of changes
   - Reference any related issues

## Development Setup

```bash
# Clone the repository
git clone https://github.com/DelwarOfficial/Lithic.git
cd Lithic

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e .[dev]
```

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints (Python 3.12+)
- Run ruff before committing:
  ```bash
  ruff check .
  ```

## Testing

- Write tests for all new functionality
- Run the test suite:
  ```bash
  pytest tests/ -v
  ```

## Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions and classes
- Keep platform guidelines up to date

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` test changes
- `chore:` maintenance tasks

Example:
```
feat: add /lithic query command

Adds the ability to query the knowledge graph using natural language.
```

## Questions?

Open an issue or reach out via [GitHub Discussions](https://github.com/DelwarOfficial/Lithic/discussions).

Thank you for contributing! 🚀
