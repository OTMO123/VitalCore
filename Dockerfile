FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies including document processing
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        libpq-dev \
        # Document processing dependencies
        tesseract-ocr \
        tesseract-ocr-eng \
        libtesseract-dev \
        # Image processing
        libimage-exiftool-perl \
        # PDF processing
        poppler-utils \
        # Additional utilities
        curl \
        wget \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-windows.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for document storage
RUN mkdir -p /app/storage/documents /app/storage/temp /app/storage/backups

# Create non-root user and set permissions
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application using the enterprise startup script
CMD ["python", "run.py"]