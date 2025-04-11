import os
import sys

# Add the project directory to the Python path
# Adjust the path if your app.py is in a subdirectory
sys.path.insert(0, os.path.dirname(__file__))

# Import the 'application' object from your main app file (app.py)
# If your main file was named differently (e.g., main.py), change 'app' below
from app import application