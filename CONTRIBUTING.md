# Contributing to Claude Code Vision

Thank you for your interest in contributing to Claude Code Vision! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Linux environment (X11 or Wayland)
- Screenshot tools: scrot (X11) or grim (Wayland)
- Region selection tools: slop (X11) or slurp (Wayland)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Patrik652/claude-code-vision.git
   cd claude-code-vision
   ```

2. **Run the installation script**
   ```bash
   ./install.sh --dev
   ```

   This will:
   - Install system dependencies
   - Create a Python virtual environment
   - Install Python dependencies (including dev dependencies)
   - Initialize the configuration

3. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

4. **Verify the installation**
   ```bash
   claude-vision --doctor
   claude-vision --test-capture
   ```

### Manual Setup (Alternative)

If you prefer manual setup:

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```

3. **Install system dependencies**
   - Ubuntu/Debian: `sudo apt install scrot slop grim slurp imagemagick`
   - Fedora: `sudo dnf install scrot slop grim slurp ImageMagick`
   - Arch: `sudo pacman -S scrot slop grim slurp imagemagick`

## Project Structure

```
claude-code-vision/
├── src/
│   ├── cli/                    # CLI command implementations
│   │   ├── main.py             # Main CLI entry point
│   │   ├── vision_command.py   # /vision command
│   │   ├── vision_area_command.py
│   │   ├── vision_auto_command.py
│   │   └── ...
│   ├── services/               # Business logic services
│   │   ├── vision_service.py   # Core vision service
│   │   ├── screenshot_capture/ # Screenshot implementations
│   │   ├── image_processor.py
│   │   ├── config_manager.py
│   │   └── ...
│   ├── interfaces/             # Interface definitions (ABC)
│   │   └── screenshot_service.py
│   ├── models/                 # Data models
│   │   └── entities.py
│   └── lib/                    # Utility libraries
│       ├── exceptions.py       # Custom exceptions
│       ├── desktop_detector.py
│       ├── tool_detector.py
│       └── logging_config.py
├── tests/
│   ├── contract/               # Contract tests (interface compliance)
│   ├── integration/            # Integration tests
│   └── unit/                   # Unit tests
├── specs/                      # SpecKit specifications
│   └── 002-claude-code-vision/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── install.sh                  # Installation script
└── README.md
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (not 79)
- **Imports**: Organized in groups (stdlib, third-party, local)
- **Type hints**: Required for all public functions
- **Docstrings**: Google-style docstrings for all public classes and methods

### Code Formatting

We use **Black** for code formatting:

```bash
black src tests
```

### Linting

We use **Ruff** for linting:

```bash
ruff check src tests
```

### Type Checking

We use **mypy** for static type checking:

```bash
mypy src
```

### Pre-commit Checklist

Before committing, ensure:

1. Code is formatted with Black
2. No linting errors from Ruff
3. Type checking passes with mypy
4. All tests pass
5. New code has tests
6. Docstrings are complete

### Example Code

```python
"""
Module docstring describing the purpose.
"""

from pathlib import Path
from typing import Optional

from src.interfaces.screenshot_service import IScreenshotCapture
from src.lib.exceptions import ScreenshotCaptureError


class MyScreenshotCapture(IScreenshotCapture):
    """
    Class implementing screenshot capture.

    Args:
        config: Configuration object
        temp_manager: Temporary file manager

    Attributes:
        config: Stored configuration
        temp_manager: File manager instance
    """

    def __init__(self, config: Configuration, temp_manager: TempFileManager):
        """Initialize the capture instance."""
        self.config = config
        self.temp_manager = temp_manager

    def capture_full_screen(self, monitor: int = 0) -> Screenshot:
        """
        Capture full screen from specified monitor.

        Args:
            monitor: Monitor index (0 = primary)

        Returns:
            Screenshot object with captured image

        Raises:
            ScreenshotCaptureError: If capture fails
        """
        # Implementation here
        pass
```

## Testing Guidelines

### Test-First Development (TDD)

We follow Test-First Development:

1. Write the test first (it should fail)
2. Implement the minimal code to make it pass
3. Refactor if needed
4. Repeat

### Test Structure

We use three types of tests:

1. **Contract Tests** (`tests/contract/`)
   - Verify interface implementations comply with contracts
   - Test that classes implement all required methods
   - Validate return types and exceptions

2. **Integration Tests** (`tests/integration/`)
   - Test multiple components working together
   - Test real file I/O, subprocess calls
   - Test full workflows

3. **Unit Tests** (`tests/unit/`)
   - Test individual functions/methods in isolation
   - Use mocks/stubs for dependencies
   - Fast execution

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_desktop_detector.py

# Run specific test
pytest tests/unit/test_desktop_detector.py::test_detect_x11

# Run with verbose output
pytest -v

# Run with output (don't capture stdout)
pytest -s
```

### Writing Tests

Example test structure:

```python
"""Tests for MyClass."""

import pytest
from unittest.mock import Mock, patch

from src.services.my_class import MyClass


class TestMyClass:
    """Test suite for MyClass."""

    def test_basic_functionality(self):
        """Test basic functionality works."""
        instance = MyClass()
        result = instance.do_something()
        assert result == expected_value

    def test_error_handling(self):
        """Test error is raised correctly."""
        instance = MyClass()
        with pytest.raises(MyError):
            instance.do_invalid_thing()

    @patch('src.services.my_class.subprocess.run')
    def test_with_mock(self, mock_run):
        """Test using mocked subprocess."""
        mock_run.return_value = Mock(returncode=0, stdout="output")
        instance = MyClass()
        result = instance.run_command()
        assert result == "output"
```

## Pull Request Process

### Before Submitting

1. **Create a new branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes**
   - Follow coding standards
   - Write tests
   - Update documentation

3. **Run the test suite**
   ```bash
   pytest
   black src tests
   ruff check src tests
   mypy src
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Use conventional commits:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test changes
   - `refactor:` - Code refactoring
   - `chore:` - Build/tooling changes

5. **Push to your fork**
   ```bash
   git push origin feature/my-new-feature
   ```

### Pull Request Guidelines

- **Title**: Clear, descriptive title following conventional commits
- **Description**: Explain what and why (not how)
- **Tests**: Include tests for new functionality
- **Documentation**: Update relevant documentation
- **Single Purpose**: One feature/fix per PR
- **Size**: Keep PRs reasonably sized (< 500 lines preferred)

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
```

## Reporting Issues

### Bug Reports

When reporting bugs, include:

1. **Environment**
   - OS and version
   - Python version
   - Desktop environment (X11/Wayland)
   - Claude Code Vision version

2. **Steps to Reproduce**
   - Detailed steps to reproduce the issue
   - Expected behavior
   - Actual behavior

3. **Logs and Output**
   - Error messages
   - Relevant log entries
   - Screenshots if applicable

4. **Diagnostic Output**
   ```bash
   claude-vision --doctor
   ```

### Feature Requests

When requesting features, include:

1. **Use Case**: Describe the problem you're trying to solve
2. **Proposed Solution**: Your idea for how to solve it
3. **Alternatives**: Other solutions you've considered
4. **Priority**: How important is this feature to you?

### Issue Template

```markdown
## Environment
- OS: Ubuntu 22.04
- Python: 3.10.6
- Desktop: X11
- Version: 0.1.0

## Description
Clear description of the issue.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Logs
```
Paste relevant logs here
```

## Diagnostic Output
```
Output from `claude-vision --doctor`
```
```

## Development Workflow

### SpecKit Methodology

This project follows the SpecKit methodology:

1. **Specify** - Define requirements in `spec.md`
2. **Clarify** - Resolve ambiguities
3. **Plan** - Create implementation plan in `plan.md`
4. **Tasks** - Break down into tasks in `tasks.md`
5. **Implement** - Execute tasks with TDD

### Architecture Principles

From our constitution (`specs/002-claude-code-vision/constitution.md`):

1. **Test-First Development** - Tests before implementation
2. **Interface-Based Architecture** - Clear contracts via ABCs
3. **Defense in Depth** - Multiple fallback mechanisms
4. **Explicit Error Handling** - Comprehensive error messages
5. **Minimal External Dependencies** - Keep it simple

## Getting Help

- **Documentation**: Check README.md and specs/
- **Issues**: Search existing issues
- **Discussions**: Start a discussion for questions
- **Doctor**: Run `claude-vision --doctor` for diagnostics

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Claude Code Vision! 🎉
