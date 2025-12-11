#!/usr/bin/env python3
"""
Setup script to create the claude-skills-watch stream and subscribe users.
Run this once before starting the bot.
"""

import os
import sys
import zulip
from pathlib import Path

def main():
    # Load API key from environment or .env file
    api_key = os.environ.get("FORMATTER_BOT_API_KEY")

    if not api_key:
        # Try to read from .env file
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('FORMATTER_BOT_API_KEY='):
                        api_key = line.strip().split('=', 1)[1]
                        break

    if not api_key:
        print("Error: FORMATTER_BOT_API_KEY not found in environment or .env file")
        sys.exit(1)

    # Create Zulip client
    client = zulip.Client(
        email='formatter-bot@chat.dollhousemcp.com',
        api_key=api_key,
        site='https://chat.dollhousemcp.com'
    )

    print("Setting up claude-skills-watch stream...")

    # Create stream (this will also subscribe the bot)
    print("1. Creating stream...")
    result = client.add_subscriptions(
        streams=[{
            'name': 'claude-skills-watch',
            'description': "Monitoring news about Anthropic's Agent Skills / Claude Skills feature for AGPL attribution tracking"
        }]
    )

    if result.get('result') == 'success':
        print("   ✓ Stream created successfully")
    else:
        print(f"   Error: {result}")
        # Continue anyway - stream might already exist

    # Subscribe user8@chat.dollhousemcp.com
    print("2. Subscribing user8@chat.dollhousemcp.com...")
    result = client.add_subscriptions(
        streams=[{'name': 'claude-skills-watch'}],
        principals=['user8@chat.dollhousemcp.com']
    )

    if result.get('result') == 'success':
        print("   ✓ User subscribed successfully")
    else:
        print(f"   Error: {result}")

    print("\nSetup complete! You can now start the claude-skills-bot:")
    print("  docker-compose up -d claude-skills-bot")

if __name__ == "__main__":
    main()
