# Contributing to ResearchDraft.ai

Thank you for your interest in contributing to ResearchDraft.ai! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or suggest features
- Include a clear description of the issue
- Provide steps to reproduce for bugs
- Include your environment (OS, Python version, etc.)

### Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run the tests:
   ```powershell
   cd research_paper_agent
   python -m py_compile service.py api.py models.py
   python -m unittest tests.test_quality_gate tests.test_export_helpers tests.test_literature_and_prompts
   ```
5. Commit your changes with a clear message
6. Push to your fork
7. Create a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Add docstrings to new functions and classes
- Keep functions focused and small
- Add type hints where appropriate

### Testing

- Add tests for new features
- Ensure existing tests pass before submitting
- Tests are in `research_paper_agent/tests/`

### Documentation

- Update README.md if adding new features
- Add inline comments for complex logic
- Update API documentation if changing endpoints

## Development Setup

1. Clone the repository:
   ```powershell
   git clone https://github.com/xiejhhhhhh/ResearchDraft.ai.git
   cd ResearchDraft.ai
   ```

2. Run the setup script:
   ```powershell
   .\scripts\setup_local.ps1
   ```

3. Edit `.env` with your API keys

4. Start the backend:
   ```powershell
   .\scripts\start_backend.ps1
   ```

5. Start the frontend:
   ```powershell
   .\scripts\start_frontend.ps1
   ```

## Questions?

Feel free to open an issue for any questions about contributing.
