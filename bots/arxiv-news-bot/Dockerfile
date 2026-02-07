FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY shared/ /app/shared/

# Copy bot files
COPY arxiv-news-bot/ /app/arxiv-news-bot/

# Install dependencies
RUN pip install --no-cache-dir -r /app/arxiv-news-bot/requirements.txt

WORKDIR /app/arxiv-news-bot

CMD ["python", "arxiv_news_bot.py"]
