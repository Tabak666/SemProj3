FROM python:3.12-slim

# Install system dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends git build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone the repository into /app
RUN git clone -b dockerfile https://github.com/Tabak666/SemProj3.git /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Expose Django default port
EXPOSE 8000

# Start Django server
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
