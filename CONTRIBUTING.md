# Contributing to Polisen Events Collector

Thank you for your interest in contributing to the Polisen Events Collector! This document provides guidelines for contributing to this project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs (with sensitive data redacted)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:

- A clear description of the enhancement
- The use case and benefits
- Any potential drawbacks or implementation challenges

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Set up your development environment**:
   ```bash
   git clone https://github.com/yourusername/polisen-events-collector.git
   cd polisen-events-collector
   cp .env.example .env
   # Edit .env with your configuration
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Make your changes**:
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure your code passes linting and tests

4. **Test your changes**:
   ```bash
   # Run tests
   pytest tests/unit -v

   # Run with coverage
   pytest tests/unit --cov=. --cov-report=term-missing

   # Run linting (if pre-commit hooks are set up)
   pre-commit run --all-files
   ```

5. **Commit your changes**:
   - Use clear, descriptive commit messages
   - Reference issue numbers when applicable
   ```bash
   git commit -m "Fix event deduplication bug (#42)"
   ```

6. **Push to your fork** and submit a pull request

7. **Wait for review**:
   - Respond to feedback
   - Make requested changes
   - Keep the discussion focused and professional

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise
- Add type hints where appropriate

### Testing

- Write unit tests for new functionality
- Aim for >80% code coverage
- Test edge cases and error conditions
- Mock external services (API calls, OCI storage)

### Documentation

- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update docstrings when changing function signatures
- Keep documentation clear and concise

### Security

- **Never commit secrets or credentials**
- Use environment variables for configuration
- Follow the security guidelines in SECURITY.md
- Report security vulnerabilities privately

### Environment Variables

When adding new configuration:

1. Add to `.env.example` with documentation
2. Update README.md setup instructions
3. Add validation in the code
4. Use sensible defaults when possible

## API Compliance

When modifying API interaction code, ensure compliance with [Polisen API rules](https://polisen.se/om-polisen/om-webbplatsen/oppna-data/regler-for-oppna-data/):

- Include User-Agent header
- Respect rate limits (max 60 calls/hour)
- Use minimum 10 seconds between calls
- Use HTTPS only

## Project Structure

```
polisen-events-collector/
├── collect_events.py      # Main collector script
├── secrets_manager.py     # OCI Vault integration
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── conftest.py       # Pytest configuration
├── logs/                  # Log files (gitignored)
├── .env.example          # Environment template
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
└── README.md             # User documentation
```

## Getting Help

- Check existing issues and pull requests
- Read the README.md and documentation
- Ask questions in issue discussions
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in the project. Thank you for making this project better!
