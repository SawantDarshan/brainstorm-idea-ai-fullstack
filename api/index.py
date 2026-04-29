import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI

app = FastAPI()

# Import and mount the actual app
from interfaces.api.api_app import app as real_app

app = real_app