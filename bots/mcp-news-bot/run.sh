#!/bin/bash
# Quick start script for MCP News Bot

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and configure your credentials"
    exit 1
fi

# Load environment variables
# shellcheck disable=SC2046
export $(grep -v '^#' .env | xargs)

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
# shellcheck disable=SC1091
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the bot
echo "Starting MCP News Bot..."
python mcp_news_bot.py "$@"
