FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY shared/ /app/shared/

# Copy bot files
COPY youtube-news-bot/ /app/youtube-news-bot/

# Install dependencies
RUN pip install --no-cache-dir -r /app/youtube-news-bot/requirements.txt

WORKDIR /app/youtube-news-bot

CMD ["python", "youtube_news_bot.py"]
