FROM python:3.13

# Set working directory
WORKDIR /app

# Install build dependencies for opencv
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .


EXPOSE 5050

CMD ["python", "app.py"]
