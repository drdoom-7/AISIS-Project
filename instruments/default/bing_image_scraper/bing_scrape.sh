#!/bin/bash

# bing_scrape.sh - A shell script wrapper for bing_image_scraper.py

# Ensure the Python script is in the same directory
SCRIPT_DIR="$(dirname "$0")"
PYTHON_SCRIPT="${SCRIPT_DIR}/bing_image_scraper.py"

# Pass all arguments to the Python script
python "$PYTHON_SCRIPT" "$@"
