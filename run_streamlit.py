#!/usr/bin/env python3
"""Launcher script for the Investment Research Streamlit app."""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["OPENAI_API_KEY", "OPENROUTER_API_KEY"]
    
    if not any(os.getenv(var) for var in required_vars):
        print("❌ Error: No API key found!")
        print("Please set one of the following environment variables:")
        print("  - OPENAI_API_KEY")
        print("  - OPENROUTER_API_KEY")
        print()
        print("You can set them by:")
        print("  export OPENROUTER_API_KEY='your-api-key'")
        print("  # or add to .env file")
        return False
    
    return True

def check_dependencies():
    """Check if required packages are installed."""
    try:
        import streamlit
        import pandas
        import pydantic_ai
        import chromadb
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print()
        print("Please install dependencies:")
        print("  pip install -e .")
        print("  # or")
        print("  poetry install")
        return False

def main():
    """Main launcher function."""
    print("🚀 Starting Investment Research System...")
    print()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Get the app path
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    # Launch Streamlit
    print("🌐 Launching Streamlit app...")
    print("📊 Investment Research System will open in your browser")
    print()
    print("To stop the app, press Ctrl+C in this terminal")
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.headless", "false",
            "--server.address", "localhost",
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\n👋 Investment Research System stopped")
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()