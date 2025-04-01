FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install build tools and system libraries for cryptography and PIL
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libjpeg-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app source
COPY . .

# Expose Flask app port
EXPOSE 5001

# Start the app using Gunicorn
CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:5001", "--timeout", "120", "wsgi:app"]
#CMD ["python", "wsgi.py"]
