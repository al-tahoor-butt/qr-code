FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for barcode generation and imaging
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "qr_architect.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
