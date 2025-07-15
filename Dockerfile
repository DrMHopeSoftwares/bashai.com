FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files (including start.sh)
COPY . /app/

# Make start.sh executable
RUN chmod +x /app/start.sh

# Expose the port Flask runs on
EXPOSE 5000

# Use start.sh as entrypoint
ENTRYPOINT ["./start.sh"]