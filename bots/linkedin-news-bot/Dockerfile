FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY shared/ /app/shared/

# Copy bot files
COPY linkedin-news-bot/ /app/linkedin-news-bot/

# Install dependencies
RUN pip install --no-cache-dir -r /app/linkedin-news-bot/requirements.txt

WORKDIR /app/linkedin-news-bot

CMD ["python", "linkedin_news_bot.py"]
