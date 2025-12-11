FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code and config
COPY merview_news_bot.py .
COPY config.yaml .

# The seen_items.json file will be created at runtime
# Mount a volume at /app for persistence if needed

CMD ["python", "merview_news_bot.py"]
