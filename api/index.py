"""
Vercel Serverless Entry Point
Wraps the Flask app for Vercel deployment.
"""
import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app

# Vercel expects the WSGI app as 'app'
app = app
