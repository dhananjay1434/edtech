FROM python:3.11-slim

# opencv-python-headless and pypdfium2 need these at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY cde ./cde
COPY migrations ./migrations
COPY run_worker.py ./

EXPOSE 8000

CMD ["uvicorn", "cde.api:app", "--host", "0.0.0.0", "--port", "8000"]
