FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install build dependencies for opencv
RUN apk add --no-cache build-base

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .


EXPOSE 5050

CMD ["python", "app.py"]
