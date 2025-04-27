# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Lint/Test Commands
- Build: `make build`
- Lint: `make lint`
- Test (all): `make test`
- Test (single): `make test TEST=test_name.py`
- Format code: `make fmt`

## Code Style Guidelines
- Follow Linux kernel coding style for C/C++ code
- PEP 8 for Python code
- Use type annotations in Python code
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Import order: standard library, third-party, local
- Function/method names: snake_case
- Class names: CamelCase
- Constants: UPPERCASE_WITH_UNDERSCORES
- Error handling: prefer early returns, use appropriate error codes
- Include descriptive docstrings for all functions and classes
- Keep functions focused on a single responsibility
- Write unit tests for all new functionality

## Project Organization
- Source code in `src/` directory
- Tests in `tests/` directory
- Documentation in `docs/` directory