# Contributing to SemWiki

Thank you for your interest in contributing to SemWiki! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/ian-m-griffiths/SemWiki.git`
3. Create a virtual environment: `python3 -m venv venv`
4. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
5. Install dev dependencies: `pip install -r requirements-dev.txt`

## How to Contribute

### Reporting Bugs

- Check if the bug has already been reported
- Include steps to reproduce
- Include Python version and OS
- Include error messages and logs
- Note: this is a demo for the capabilities of SemWiki - It was coded with an AI, with human guidance for architecture including vast majority of documentation.

### Suggesting Features

- Open an issue with the "enhancement" label
- Describe the use case
- Explain why it would be useful

### Pull Requests

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Add tests if applicable
4. Update documentation
5. Commit with clear messages
6. Push to your fork
7. Open a pull request

## Code Style - Follow PEP 8

- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

## Testing

Run tests with: `pytest tests/`

## Questions?

Open an issue or join our discussions!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
