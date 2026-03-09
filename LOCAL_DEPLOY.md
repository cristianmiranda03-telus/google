# Local Deployment Guide

This project includes a convenient launcher script (`run.py`) that handles the entire local deployment process for both the frontend and backend.

## Prerequisites

Before running the script, ensure you have the following installed on your system:
- **Python 3.x**
- **Node.js** (and npm)

## Configuration

1. Navigate to the `backend` directory.
2. Create a `.env` file (you can copy from `.env.example` if available).
3. Ensure you have set your API key in the `.env` file:
   ```env
   FUELIX_API_KEY=your_actual_api_key_here
   ```

## Running the Application

To start the application locally, open your terminal, navigate to the `cv_review` directory, and run:

```bash
python run.py
```

### What `run.py` does automatically:

1. **System Checks**: Verifies that Node.js is installed and accessible.
2. **Backend Setup**: 
   - Creates a Python virtual environment (`.venv`) inside the `backend/` directory.
   - Installs all required Python dependencies from `backend/requirements.txt` (or fallback essentials).
   - Warns you if your `.env` file or API key is missing.
3. **Frontend Setup**:
   - Automatically runs `npm install` inside the `frontend/` directory if the `node_modules` folder is missing.
4. **Starts Servers**:
   - Launches the **FastAPI backend** on `http://localhost:8000`.
   - Launches the **Next.js frontend** on `http://localhost:3000`.
5. **Log Management**: Streams and color-codes logs from both the frontend (`[WEB]`) and backend (`[API]`) directly into your terminal.
6. **Auto-Restart**: Monitors the processes and automatically restarts them if either one crashes.

## Accessing the Application

Once the script successfully completes its setup and displays `[READY] App is running:`, you can access:
- **Web Interface (Next.js)**: [http://localhost:3000](http://localhost:3000)
- **API Documentation (FastAPI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Stopping the Servers

To gracefully stop both the frontend and backend servers, simply press `Ctrl+C` in the terminal where the script is running. The script will handle shutting down both processes cleanly.