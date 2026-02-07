FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code and config
COPY merview_digest_bot.py .
COPY config.yaml .

CMD ["python", "merview_digest_bot.py"]
