#!/usr/bin/env python3
"""Windows-safe entry point for the paired quick benchmark.

Antigravity CLI can briefly retain a handle to the disposable benchmark workspace after the
subprocess exits. On Windows that can make tempfile.TemporaryDirectory cleanup raise WinError 32/5
and abort an otherwise completed benchmark result. This wrapper changes cleanup only: temporary
workspace deletion becomes best-effort while the benchmark protocol, prompts, judge, scorer,
plugin condition, fingerprints, and result handling remain owned by run_pair.py/run_antigravity.py.
"""
from __future__ import annotations

import tempfile


_StdTemporaryDirectory = tempfile.TemporaryDirectory


class _WindowsSafeTemporaryDirectory(_StdTemporaryDirectory):
    def __init__(self, *args, **kwargs):
        kwargs["ignore_cleanup_errors"] = True
        super().__init__(*args, **kwargs)


tempfile.TemporaryDirectory = _WindowsSafeTemporaryDirectory

import run_pair  # noqa: E402  (patch tempfile before importing the benchmark runner)


if __name__ == "__main__":
    run_pair.main()
