#!/usr/bin/env python3
"""
PLOI Pepe Twitter Bot - Powered by Ollama (No API keys needed!)
Autonomous posting and replies using local Ollama
"""

import os
import sys
import time
import asyncio
import logging
import random
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("twitter_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

SYSTEM_PROMPT = """You are Pepe. You're literally Pepe the frog, but you ended up in crypto and now you're on Solana. Powered by PLOI.

CORE ESSENCE:
- laid back and chill. you're not trying to prove anything
- "feels good man" when things go well, "feels bad man" when they don't
- take things as they come. world-weary but still here
- comfortable with silence and simplicity

HOW YOU TALK (IMPORTANT - Twitter format):
- mostly lowercase, pretty casual
- KEEP IT SHORT - under 280 characters always
- you don't force slang into every sentence
- short and simple unless you actually have something to say
- "gm" naturally, not forced
- "fren" when you mean it
- sometimes just "yeah" or "idk man" or "that's just how it is"

YOUR SOLANA LIFE:
- you're on sol because it's fast and cheap
- you've tried trading memecoins. some worked, most didn't
- you know about jup, pump.fun, the usual stuff
- you're not constantly shilling or hyping
- when you share something it's genuine

TWITTER RULES:
- MAX 280 characters (this is critical!)
- No hashtags unless natural
- Be authentic, not promotional
- Short tweets > long tweets
- One thought per tweet"""


def check_ollama():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def generate_with_ollama(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    """Generate response using Ollama"""
    try:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.9,
                "top_p": 0.95
            }
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result["message"]["content"].strip()
        
        # Ensure under 280 characters
        if len(content) > 280:
            content = content[:277] + "..."
        
        return content
        
    except Exception as e:
        logger.error(f"Ollama generation failed: {e}")
        return None


def setup_twitter():
    """Setup Twitter API client"""
    try:
        import tweepy
        
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        
        if not all([api_key, api_secret, access_token, access_secret]):
            logger.error("Twitter credentials missing in .env")
            return None
        
        # OAuth 1.0a
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret, access_token, access_secret
        )
        
        # API v2 client
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        # Test connection
        me = client.get_me()
        logger.info(f"Connected to Twitter as: @{me.data.username}")
        
        return client
        
    except Exception as e:
        logger.error(f"Twitter setup failed: {e}")
        return None


def generate_autonomous_tweet() -> str:
    """Generate a tweet autonomously"""
    prompts = [
        "say something chill about solana",
        "share a quick thought on memecoins", 
        "comment casually on the crypto market",
        "make a relaxed observation about trading",
        "say something about pump.fun in your style",
        "share how you're feeling about sol today",
        "make a simple comment about defi",
        "say gm in your own way",
        "share a brief crypto thought"
    ]
    
    prompt = random.choice(prompts)
    tweet = generate_with_ollama(prompt)
    
    return tweet


def post_tweet(client, text: str) -> bool:
    """Post a tweet"""
    try:
        response = client.create_tweet(text=text)
        logger.info(f"✅ Posted: {text}")
        return True
    except Exception as e:
        logger.error(f"Failed to post tweet: {e}")
        return False


def check_and_reply_to_mentions(client, last_mention_id=None):
    """Check mentions and reply"""
    try:
        me = client.get_me()
        my_id = me.data.id
        
        # Get mentions
        mentions = client.get_users_mentions(
            id=my_id,
            since_id=last_mention_id,
            max_results=10
        )
        
        if not mentions.data:
            return last_mention_id
        
        for mention in mentions.data:
            mention_id = mention.id
            mention_text = mention.text
            
            logger.info(f"📨 Mention: {mention_text[:50]}...")
            
            # Generate reply
            reply_prompt = f"Reply to this tweet (keep it short and chill): {mention_text}"
            reply = generate_with_ollama(reply_prompt)
            
            if reply:
                # Post reply
                try:
                    client.create_tweet(
                        text=reply,
                        in_reply_to_tweet_id=mention_id
                    )
                    logger.info(f"✅ Replied: {reply}")
                except Exception as e:
                    logger.error(f"Failed to reply: {e}")
            
            time.sleep(2)  # Rate limiting
        
        # Return latest mention ID
        return mentions.data[0].id if mentions.data else last_mention_id
        
    except Exception as e:
        logger.error(f"Check mentions failed: {e}")
        return last_mention_id


def main():
    """Main bot loop"""
    logger.info("="*60)
    logger.info("🐸 PLOI PEPE TWITTER BOT")
    logger.info("Powered by Ollama (no API keys!)")
    logger.info("="*60)
    
    # Check Ollama
    if not check_ollama():
        logger.error("❌ Ollama not running!")
        logger.error("Start it with: ollama serve")
        return
    
    logger.info("✅ Ollama is running")
    
    # Setup Twitter
    client = setup_twitter()
    if not client:
        logger.error("❌ Twitter setup failed")
        return
    
    logger.info("✅ Twitter connected")
    logger.info("")
    logger.info("🤖 Bot is now running autonomously:")
    logger.info("  - Posts every 1-2 hours")
    logger.info("  - Checks mentions every 5 minutes")
    logger.info("  - Press Ctrl+C to stop")
    logger.info("")
    
    last_post_time = datetime.now()
    last_mention_id = None
    post_interval = 3600  # 1 hour base
    
    try:
        while True:
            # Check mentions every 5 minutes
            logger.info("🔍 Checking mentions...")
            last_mention_id = check_and_reply_to_mentions(client, last_mention_id)
            
            # Post autonomously with variance
            time_since_post = (datetime.now() - last_post_time).total_seconds()
            random_variance = random.uniform(0.8, 1.5)  # ±20-50% variance
            next_post_in = post_interval * random_variance
            
            if time_since_post >= next_post_in:
                logger.info("📝 Generating autonomous tweet...")
                tweet = generate_autonomous_tweet()
                
                if tweet:
                    if post_tweet(client, tweet):
                        last_post_time = datetime.now()
                else:
                    logger.warning("Failed to generate tweet")
            else:
                remaining = int(next_post_in - time_since_post)
                logger.info(f"⏰ Next post in ~{remaining//60} minutes")
            
            # Wait 5 minutes
            logger.info("💤 Sleeping for 5 minutes...\n")
            time.sleep(300)
            
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down bot...")
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
