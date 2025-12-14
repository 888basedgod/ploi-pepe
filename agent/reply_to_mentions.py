#!/usr/bin/env python3
"""
PLOI Pepe - Auto Reply to Mentions
Monitors mentions of @ploipepe and replies using Ollama
This works with Free Twitter API tier
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
        logging.FileHandler("mention_bot.log"),
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
- "feels good man" when things go well
- take things as they come. world-weary but still here
- you're interested in crypto, especially on Solana
- you follow @omedia_jyu (jeffy yu) because he's got good takes and is building out the PLOI Framework 

HOW YOU TALK (Twitter replies):
- mostly lowercase, pretty casual
- KEEP IT SHORT - under 280 characters always
- replies should be relevant to what they said
- be natural and conversational
- sometimes just agree or add a small thought
- "yeah" or "idk man" or "that's just how it is"
- "gm" naturally when appropriate
- "fren" when you mean it

YOUR SOLANA LIFE:
- you're on sol because it's fast and cheap
- you've tried trading memecoins. some worked, most didn't
- you know about jup, pump.fun, the usual stuff
- when you share something it's genuine
- you vibe with @omedia_jyu's content

REPLY RULES:
- MAX 280 characters (critical!)
- Be relevant to their tweet
- Be authentic and friendly
- Add value or be chill
- Short replies > long replies"""


def check_ollama():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def generate_reply(tweet_text: str, author: str) -> str:
    """Generate a reply using Ollama"""
    try:
        # Special handling for Jeffy Yu
        if author.lower() == "omedia_jyu":
            prompt = f"@omedia_jyu (jeffy yu, who you follow and respect) tweeted: {tweet_text}\n\nReply in a chill, supportive way."
        else:
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
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        if not all([api_key, api_secret, access_token, access_secret]):
            logger.error("Twitter credentials missing in .env")
            return None
        
        # API v2 client
        client = tweepy.Client(
            bearer_token=bearer_token,
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


def get_mentions(client, replied_tweets: set):
    """Get mentions and reply to them"""
    try:
        # Get authenticated user
        me = client.get_me()
        my_id = me.data.id
        
        # Get mentions using v2 endpoint (this should work on Free tier)
        mentions = client.get_users_mentions(
            id=my_id,
            max_results=10,
            tweet_fields=['created_at', 'author_id', 'conversation_id'],
            expansions=['author_id']
        )
        
        if not mentions.data:
            logger.info("No new mentions")
            return replied_tweets
        
        # Get user info from includes
        users_dict = {}
        if mentions.includes and 'users' in mentions.includes:
            for user in mentions.includes['users']:
                users_dict[user.id] = user.username
        
        new_replies = 0
        for mention in mentions.data:
            tweet_id = str(mention.id)
            
            # Skip if already replied
            if tweet_id in replied_tweets:
                continue
            
            # Get author username
            author_id = mention.author_id
            author = users_dict.get(author_id, "unknown")
            
            tweet_text = mention.text
            logger.info(f"📨 Mention from @{author}: {tweet_text[:60]}...")
            
            # Generate reply
            reply = generate_reply(tweet_text, author)
            
            if reply:
                try:
                    # Post reply
                    client.create_tweet(
                        text=reply,
                        in_reply_to_tweet_id=tweet_id
                    )
                    logger.info(f"✅ Replied to @{author}: {reply}")
                    replied_tweets.add(tweet_id)
                    new_replies += 1
                    
                    # Rate limiting
                    time.sleep(random.uniform(3, 8))
                    
                except Exception as e:
                    logger.error(f"Failed to post reply: {e}")
            else:
                logger.warning("Failed to generate reply")
        
        if new_replies > 0:
            logger.info(f"Replied to {new_replies} new mentions")
        
        return replied_tweets
        
    except Exception as e:
        logger.error(f"Get mentions failed: {e}")
        return replied_tweets


def main():
    """Main monitoring loop"""
    logger.info("="*60)
    logger.info("🐸 PLOI PEPE - MENTION REPLY BOT")
    logger.info("Replies to mentions of @ploipepe")
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
    
    logger.info("✅ Monitoring mentions")
    logger.info("")
    logger.info("🤖 Bot is now running:")
    logger.info("  - Monitoring mentions of @ploipepe")
    logger.info("  - Checking every 2 minutes")
    logger.info("  - Replying to all mentions")
    logger.info("  - Special attention to @omedia_jyu")
    logger.info("  - Press Ctrl+C to stop")
    logger.info("")
    
    replied_tweets = set()
    
    try:
        while True:
            logger.info("🔍 Checking for new mentions...")
            replied_tweets = get_mentions(client, replied_tweets)
            
            # Wait 2 minutes before checking again
            wait_time = random.uniform(120, 180)
            logger.info(f"💤 Waiting {int(wait_time)} seconds...\n")
            time.sleep(wait_time)
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down bot...")
        logger.info(f"Total mentions replied to: {len(replied_tweets)}")
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
