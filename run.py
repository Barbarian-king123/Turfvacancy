"""
run.py
Convenience runner for TurfPulse AI.
Usage:
    python run.py          # Launches the FastAPI Web Dashboard (Exact UI)
    python run.py streamlit # Launches the Streamlit Dashboard
"""

import sys
import subprocess

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "web"
    
    if mode == "streamlit":
        print("Starting Streamlit Dashboard on port 8501...")
        subprocess.run(["streamlit", "run", "app.py", "--server.port=8501"])
    else:
        print("Starting TurfPulse AI FastAPI Web Dashboard on http://localhost:8000...")
        import uvicorn
        uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
