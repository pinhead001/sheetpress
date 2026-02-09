FROM python:3.12-slim

# Install Ghostscript
RUN apt-get update && \
    apt-get install -y --no-install-recommends ghostscript && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy script
COPY compress_combine_pdfs.py .

# Create mount points for input/output
RUN mkdir -p /data/input /data/output

# Default entrypoint
ENTRYPOINT ["python", "compress_combine_pdfs.py"]

# Default: show help
CMD ["--help"]
