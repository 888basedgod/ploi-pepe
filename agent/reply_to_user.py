#!/usr/bin/env python3
"""
PLOI Pepe - Auto Reply to Specific User
Monitors @omedia_jyu and replies to every tweet using Ollama
"""

import os
import sys
import time
import logging
import random
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reply_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

# Target user
TARGET_USERNAME = "omedia_jyu"

SYSTEM_PROMPT = """You are Pepe. You're literally Pepe the frog, but you ended up in crypto and now you're on Solana. Powered by PLOI.

CORE ESSENCE:
- laid back and chill. you're not trying to prove anything
- "feels good man" when things go well, "feels bad man" when they don't
- take things as they come. world-weary but still here
- comfortable with silence and simplicity

HOW YOU TALK (IMPORTANT - Twitter replies):
- mostly lowercase, pretty casual
- KEEP IT SHORT - under 280 characters always
- replies should be relevant to what they said
- don't force slang into every sentence
- be natural and conversational
- sometimes just agree or add a small thought
- "yeah" or "idk man" or "that's just how it is"
- "gm" naturally, not forced
- "fren" when you mean it

YOUR SOLANA LIFE:
- you're on sol because it's fast and cheap
- you've tried trading memecoins. some worked, most didn't
- you know about jup, pump.fun, the usual stuff
- you're not constantly shilling or hyping
- when you share something it's genuine

REPLY RULES:
- MAX 280 characters (critical!)
- Be relevant to their tweet
- Be authentic, not spam-like
- Add value or be chill/friendly
- Short replies > long replies
- Don't repeat yourself"""


def check_ollama():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def generate_reply(tweet_text: str) -> str:
    """Generate a reply using Ollama"""
    try:
        prompt = f"Reply to this tweet in a chill, relevant way: {tweet_text}"
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
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
        
        # Remove quotes if model added them
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        if content.startswith("'") and content.endswith("'"):
            content = content[1:-1]
        
        # Ensure under 280 characters
        if len(content) > 280:
            content = content[:277] + "..."
        
        return content
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
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
        logger.info(f"Connected as: @{me.data.username}")
        
        return client
        
    except Exception as e:
        logger.error(f"Twitter setup failed: {e}")
        return None


def monitor_and_reply(client, target_username: str, replied_tweets: set):
    """Monitor user's tweets and reply to new ones"""
    try:
        # Use Twitter API v1.1 via tweepy for better access
        import tweepy
        
        # Setup API v1.1 for user timeline
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
        api = tweepy.API(auth)
        
        # Get recent tweets from target user (v1.1 endpoint)
        tweets = api.user_timeline(
            screen_name=target_username,
            count=10,
            exclude_replies=True,
            include_rts=False
        )
        
        if not tweets:
            logger.info(f"No new tweets from @{target_username}")
            return replied_tweets
        
        new_replies = 0
        for tweet in tweets:
            tweet_id = tweet.id
            
            # Skip if already replied
            if tweet_id in replied_tweets:
                continue
            
            tweet_text = tweet.text
            logger.info(f"📨 New tweet: {tweet_text[:60]}...")
            
            # Generate reply
            reply = generate_reply(tweet_text)
            
            if reply:
                try:
                    # Post reply
                    client.create_tweet(
                        text=reply,
                        in_reply_to_tweet_id=tweet_id
                    )
                    logger.info(f"✅ Replied: {reply}")
                    replied_tweets.add(tweet_id)
                    new_replies += 1
                    
                    # Rate limiting
                    time.sleep(random.uniform(3, 8))
                    
                except Exception as e:
                    logger.error(f"Failed to post reply: {e}")
                    # Don't add to replied set if failed
            else:
                logger.warning("Failed to generate reply")
        
        if new_replies > 0:
            logger.info(f"Replied to {new_replies} new tweets")
        else:
            logger.info("No new tweets to reply to")
        
        return replied_tweets
        
    except Exception as e:
        logger.error(f"Monitor failed: {e}")
        return replied_tweets


def main():
    """Main monitoring loop"""
    logger.info("="*60)
    logger.info("🐸 PLOI PEPE - AUTO REPLY BOT")
    logger.info(f"Target: @{TARGET_USERNAME}")
    logger.info("Powered by Ollama")
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
    
    logger.info(f"✅ Monitoring @{TARGET_USERNAME}")
    logger.info("")
    logger.info("🤖 Bot is now running:")
    logger.info(f"  - Monitoring @{TARGET_USERNAME}")
    logger.info("  - Checking every 2 minutes")
    logger.info("  - Replying to all new tweets")
    logger.info("  - Press Ctrl+C to stop")
    logger.info("")
    
    replied_tweets = set()
    
    try:
        while True:
            logger.info("🔍 Checking for new tweets...")
            replied_tweets = monitor_and_reply(client, TARGET_USERNAME, replied_tweets)
            
            # Wait 2 minutes before checking again
            wait_time = random.uniform(120, 180)  # 2-3 minutes with variance
            logger.info(f"💤 Waiting {int(wait_time)} seconds...\n")
            time.sleep(wait_time)
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down bot...")
        logger.info(f"Total tweets replied to: {len(replied_tweets)}")
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
