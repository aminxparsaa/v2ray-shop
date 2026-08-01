FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-telegram-bot

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run both Flask and Bot
CMD ["sh", "-c", "python app.py & python bot.py"]
