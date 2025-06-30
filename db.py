#!/usr/bin/env python3
"""
db.py

Database helper for Log Analyzer & Fixer.
Handles loading and saving the known_fixes.json database.
"""
import json
import os

# Ensure DB_FILE is always in the project directory, regardless of CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'known_fixes.json')


def load_db():
    """Load known fixes from JSON file, or return empty dict if file is missing or invalid."""
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_db(db):
    """Save known fixes to JSON file."""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(db, f, indent=2)
    except IOError as e:
        print(f"Error saving database: {e}")
