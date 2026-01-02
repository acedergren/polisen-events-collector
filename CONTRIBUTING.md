# Contributing to Polisen Events Collector

Thank you for considering contributing to this project! This document provides guidelines for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and environment details

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:
- Clear description of the feature
- Use case and benefits
- Potential implementation approach

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests if available
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide for Python code
- Add docstrings for functions and classes
- Keep functions focused and single-purpose
- Comment complex logic
- Respect the Polisen API usage rules

### API Compliance

Any changes that interact with the Polisen API must:
- Maintain minimum 10-second intervals (we use 30 minutes)
- Include proper User-Agent headers
- Use HTTPS only
- Handle rate limiting gracefully

### Testing

- Test your changes locally before submitting
- Verify OCI connectivity works
- Check logs for errors
- Ensure deduplication still functions correctly

## Questions?

Feel free to open an issue for any questions or concerns.
