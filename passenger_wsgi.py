import sys, os
import importlib.util

# Add the application directory to the Python path
INTERP = "/usr/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Path to your app
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

# Import your Flask app from the root directory
from app import app as application