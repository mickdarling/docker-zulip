FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY shared/ /app/shared/

# Copy bot files
COPY bluesky-news-bot/ /app/bluesky-news-bot/

# Install dependencies
RUN pip install --no-cache-dir -r /app/bluesky-news-bot/requirements.txt

WORKDIR /app/bluesky-news-bot

CMD ["python", "bluesky_news_bot.py"]
