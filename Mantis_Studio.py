#!/usr/bin/env python3
"""Streamlit entrypoint shim for MANTIS Studio."""

from mantis.app import run_app


if __name__ == "__main__":
    raise SystemExit(run_app())
