FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY formatter_bot.py .
COPY config.yaml .

# Run the bot
CMD ["python", "formatter_bot.py"]
