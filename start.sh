#!/bin/bash
# Start the background worker process
python -m cde.jobs.worker &
# Start the FastAPI web server
uvicorn cde.api:app --host 0.0.0.0 --port $PORT
