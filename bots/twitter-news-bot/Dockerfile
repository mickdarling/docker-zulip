FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY shared/ /app/shared/

# Copy bot files
COPY twitter-news-bot/ /app/twitter-news-bot/

# Install dependencies
RUN pip install --no-cache-dir -r /app/twitter-news-bot/requirements.txt

WORKDIR /app/twitter-news-bot

CMD ["python", "twitter_news_bot.py"]
