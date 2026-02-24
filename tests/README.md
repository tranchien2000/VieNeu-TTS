# VieNeu-TTS Testing Directory

This directory contains test suites and utilities for verifying the VieNeu-TTS package.

## Test Suites

### [test_normalize.py](test_normalize.py)
A comprehensive test suite for the Vietnamese text normalization pipeline...

## How to run tests

Ensure you are in the project root:

Using `uv` (recommended):
```bash
uv run python tests/test_normalize.py
```

Using standard `python`:
```bash
python -m tests.test_normalize
```

Results are printed to the console and saved to `tests/test_results.txt`.
