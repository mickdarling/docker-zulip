FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code and config
COPY email_notifier.py .
COPY config.yaml .

# Credentials will be mounted at runtime
# - /app/credentials.json (OAuth client credentials)
# - /app/token.json (will be created after first auth)

CMD ["python", "email_notifier.py"]
