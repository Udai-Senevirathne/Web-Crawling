import sys
import os

# Add project root to path so 'backend' package is importable on Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.main import app  # noqa: F401 - Vercel uses this 'app' variable
