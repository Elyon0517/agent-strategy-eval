# Validation

## 0.1.0 — October 9, 2026

- Python 3.12.13 on macOS: 10 passed.
- Ruff lint and format checks, strict mypy, examples and source/wheel builds passed.
- Service-free examples use synthetic records, not production data.

Tests cover fixture checks, distinct baseline behavior, unscored cases, strategy errors, invalid token counts, fixture conflicts and CLI JSON output. Synthetic fixture pass rates do not establish real model success or superiority of a memory strategy.

Packages are distributed through pinned GitHub releases, not a PyPI publication. Passing these checks does not establish compatibility with every Python version, production scale or downstream model behavior.
