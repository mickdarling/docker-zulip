FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY shared/ /app/shared/

# Copy bot files
COPY mastodon-news-bot/ /app/mastodon-news-bot/

# Install dependencies
RUN pip install --no-cache-dir -r /app/mastodon-news-bot/requirements.txt

WORKDIR /app/mastodon-news-bot

CMD ["python", "mastodon_news_bot.py"]
