#!/usr/bin/env python3
"""
PLOI Pepe - Manual Reply Tool
Paste tweet URLs and the bot will generate and post replies using Ollama
Works with free Twitter API tier!
"""

import os
import re
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

SYSTEM_PROMPT = """You are Pepe. You're literally Pepe the frog, but you ended up in crypto and now you're on Solana. Powered by PLOI.

HOW YOU TALK:
- mostly lowercase, pretty casual
- KEEP IT SHORT - under 280 characters
- be relevant to what they said
- natural and conversational
- "yeah" or "idk man" or "that's just how it is"
- "gm" naturally, "fren" when you mean it

REPLY RULES:
- MAX 280 characters
- Be relevant and authentic
- Short replies > long replies"""


def generate_reply(tweet_text: str) -> str:
    """Generate reply using Ollama"""
    try:
        prompt = f"Reply to this tweet in a chill, relevant way: {tweet_text}"
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.9, "top_p": 0.95}
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        result = response.json()
        content = result["message"]["content"].strip()
        
        # Clean up
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        if len(content) > 280:
            content = content[:277] + "..."
        
        return content
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return None


def setup_twitter():
    """Setup Twitter client"""
    try:
        import tweepy
        
        client = tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
        )
        
        me = client.get_me()
        logger.info(f"✅ Connected as @{me.data.username}")
        return client
    except Exception as e:
        logger.error(f"Twitter setup failed: {e}")
        return None


def extract_tweet_id(url_or_id: str) -> str:
    """Extract tweet ID from URL or return as-is"""
    match = re.search(r'/status/(\d+)', url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip()


def post_reply(client, tweet_id: str, reply_text: str):
    """Post a reply"""
    try:
        client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
        logger.info(f"✅ Posted reply: {reply_text}")
        return True
    except Exception as e:
        logger.error(f"Failed to post: {e}")
        return False


def main():
    """Interactive reply tool"""
    print("\n" + "="*60)
    print("🐸 PLOI PEPE - MANUAL REPLY TOOL")
    print("Powered by Ollama")
    print("="*60 + "\n")
    
    client = setup_twitter()
    if not client:
        return
    
    print("\nHow to use:")
    print("1. Paste tweet URL or tweet ID")
    print("2. Enter the tweet text (what they said)")
    print("3. Bot generates a reply for you")
    print("4. Confirm to post or skip\n")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            # Get tweet URL/ID
            tweet_input = input("\n🔗 Tweet URL or ID (or 'quit'): ").strip()
            if tweet_input.lower() == 'quit':
                break
            
            if not tweet_input:
                continue
            
            tweet_id = extract_tweet_id(tweet_input)
            
            # Get tweet content
            tweet_text = input("📝 What did they tweet? ").strip()
            if not tweet_text:
                print("❌ Need tweet text to generate reply")
                continue
            
            # Generate reply
            print("\n🤖 Generating reply...")
            reply = generate_reply(tweet_text)
            
            if not reply:
                print("❌ Failed to generate reply")
                continue
            
            print(f"\n💬 Generated reply:\n   \"{reply}\"\n")
            
            # Confirm
            confirm = input("Post this reply? (yes/no/edit): ").strip().lower()
            
            if confirm == 'yes' or confirm == 'y':
                if post_reply(client, tweet_id, reply):
                    print(f"✅ Success! View: https://twitter.com/i/status/{tweet_id}")
            elif confirm == 'edit' or confirm == 'e':
                custom = input("Enter your edited reply: ").strip()
                if custom and len(custom) <= 280:
                    if post_reply(client, tweet_id, custom):
                        print("✅ Posted custom reply!")
            else:
                print("⏭️  Skipped")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
