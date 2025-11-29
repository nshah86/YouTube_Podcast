#!/usr/bin/env python3
"""
Production WSGI entrypoint for VideoTranscript Pro.

Use this file with a WSGI server such as gunicorn or waitress, e.g.:

  gunicorn -w 4 -b 0.0.0.0:5000 run:app
"""

import os

from app import app  # noqa: F401

# Ensure the correct environment is set for production
os.environ.setdefault("APP_ENV", "production")

