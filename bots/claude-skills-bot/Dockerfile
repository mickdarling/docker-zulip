FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code and config
COPY claude_skills_bot.py .
COPY config.yaml .

# The seen_items.json file will be created at runtime and mounted as a volume

CMD ["python", "claude_skills_bot.py"]
