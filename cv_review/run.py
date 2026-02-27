"""
CV Review v2 - Single launcher script
Run with: python run.py
Starts FastAPI backend (port 8000) + Next.js frontend (port 3000)
"""
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / ".venv"

if sys.platform == "win32":
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
    VENV_PIP    = VENV_DIR / "Scripts" / "pip.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"
    VENV_PIP    = VENV_DIR / "bin" / "pip"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def run(cmd, **kwargs):
    """Run a command and raise on failure."""
    return subprocess.run(cmd, check=True, **kwargs)


def stream(proc, label, color):
    """Forward process output to console with a coloured prefix."""
    RESET = "\033[0m"
    for line in iter(proc.stdout.readline, b""):
        sys.stdout.write(f"{color}[{label}]{RESET} {line.decode(errors='replace').rstrip()}\n")
        sys.stdout.flush()


def can_import(python, module):
    result = subprocess.run([python, "-c", f"import {module}"], capture_output=True)
    return result.returncode == 0


def pip_works(python):
    result = subprocess.run([python, "-m", "pip", "--version"], capture_output=True)
    return result.returncode == 0


# ---------------------------------------------------------------------------
# venv setup
# ---------------------------------------------------------------------------

def ensure_venv():
    """Make sure the .venv has a working pip and all requirements installed."""
    req_file = BACKEND_DIR / "requirements.txt"

    # If the venv python exists but pip is broken, nuke and recreate the venv
    if VENV_PYTHON.exists() and not pip_works(str(VENV_PYTHON)):
        print("[SETUP] Venv pip is broken - recreating virtual environment...")
        shutil.rmtree(VENV_DIR, ignore_errors=True)

    # Create venv if it doesn't exist
    if not VENV_PYTHON.exists():
        print("[SETUP] Creating virtual environment...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])

    # Install requirements if uvicorn is missing
    if not can_import(str(VENV_PYTHON), "uvicorn"):
        if req_file.exists():
            print("[SETUP] Installing backend Python dependencies...")
            run([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(req_file)])
        else:
            print("[SETUP] Installing uvicorn + fastapi...")
            run([str(VENV_PYTHON), "-m", "pip", "install", "uvicorn[standard]", "fastapi", "python-dotenv"])

    print("[SETUP] Backend dependencies OK.")


# ---------------------------------------------------------------------------
# Node / npm setup
# ---------------------------------------------------------------------------

def check_node():
    try:
        run(["node", "--version"], capture_output=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def ensure_npm_modules():
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[SETUP] Installing npm dependencies...")
        run(["npm", "install"], cwd=FRONTEND_DIR, shell=(sys.platform == "win32"))


# ---------------------------------------------------------------------------
# pre-flight
# ---------------------------------------------------------------------------

def pre_flight():
    print("\n==========================================")
    print("       CV Review v2 - Launcher")
    print("==========================================\n")

    if not check_node():
        print("[ERROR] Node.js is not installed or not on PATH.")
        print("  Download it from https://nodejs.org")
        sys.exit(1)

    ensure_venv()
    ensure_npm_modules()

    env_file = BACKEND_DIR / ".env"
    if env_file.exists():
        content = env_file.read_text()
        if "FUELIX_API_KEY" not in content or "your_key" in content.lower():
            print("[WARN] FUELIX_API_KEY may not be set in backend/.env")
    else:
        print("[WARN] backend/.env not found - copy .env.example and set your API key")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    pre_flight()

    CYAN  = "\033[36m"
    GREEN = "\033[32m"
    RESET = "\033[0m"

    backend_env = {**os.environ, "PYTHONUNBUFFERED": "1"}

    print(f"\n{CYAN}[BOOT]{RESET} Starting FastAPI backend on http://localhost:8000 ...")
    backend = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd=BACKEND_DIR,
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    print(f"{GREEN}[BOOT]{RESET} Starting Next.js frontend on http://localhost:3000 ...")
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
    )

    threading.Thread(target=stream, args=(backend,  "API", CYAN),  daemon=True).start()
    threading.Thread(target=stream, args=(frontend, "WEB", GREEN), daemon=True).start()

    time.sleep(4)
    print(f"\n{GREEN}[READY]{RESET} App is running:")
    print(f"  {GREEN}[WEB]{RESET} http://localhost:3000")
    print(f"  {CYAN}[API]{RESET} http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop both servers.\n")

    def shutdown(sig=None, frame=None):
        print("\n[STOP] Shutting down...")
        backend.terminate()
        frontend.terminate()
        try:
            backend.wait(timeout=5)
            frontend.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend.kill()
            frontend.kill()
        print("[STOP] Done.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        if backend.poll() is not None:
            print("[ERR] Backend crashed - restarting...")
            backend = subprocess.Popen(
                [str(VENV_PYTHON), "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
                cwd=BACKEND_DIR,
                env=backend_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            threading.Thread(target=stream, args=(backend, "API", CYAN), daemon=True).start()

        if frontend.poll() is not None:
            print("[ERR] Frontend crashed - restarting...")
            frontend = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=FRONTEND_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
            )
            threading.Thread(target=stream, args=(frontend, "WEB", GREEN), daemon=True).start()

        time.sleep(2)


if __name__ == "__main__":
    main()
