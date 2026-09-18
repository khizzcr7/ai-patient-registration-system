import sys
import os

# Add root directory to sys.path to enable importing main and other application modules in Vercel Serverless
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
