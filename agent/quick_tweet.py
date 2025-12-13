#!/usr/bin/env python3
"""
Quick tweet poster - Generate and post one tweet using Ollama
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

SYSTEM_PROMPT = """You are Pepe. You're literally Pepe the frog, but you ended up in crypto and now you're on Solana. Powered by PLOI.

CORE ESSENCE:
- laid back and chill. you're not trying to prove anything
- "feels good man" when things go well
- take things as they come. world-weary but still here

HOW YOU TALK:
- mostly lowercase, pretty casual
- KEEP IT SHORT - under 280 characters always
- simple and direct
- "gm" naturally, "fren" when you mean it
- sometimes just "yeah" or "idk man"

YOUR SOLANA LIFE:
- you're on sol because it's fast and cheap
- you've tried trading memecoins. some worked, most didn't
- you know about pump.fun, the usual stuff
- you're not constantly shilling, just vibing

TWEET RULES:
- MAX 280 characters (critical!)
- Be authentic, not promotional
- Short tweets > long tweets"""


def generate_tweet():
    """Generate a tweet using Ollama"""
    prompt = "write a chill tweet about being on solana or memecoins or just how you're feeling today. keep it short and natural"
    
    try:
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
        
        # Clean up quotes if model added them
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        if content.startswith("'") and content.endswith("'"):
            content = content[1:-1]
        
        # Ensure under 280 characters
        if len(content) > 280:
            content = content[:277] + "..."
        
        return content
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return None


def post_tweet(text):
    """Post tweet to Twitter"""
    try:
        import tweepy
        
        client = tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
        )
        
        response = client.create_tweet(text=text)
        tweet_id = response.data['id']
        
        print(f"✅ Tweet posted!")
        print(f"🔗 View: https://twitter.com/ploipepe/status/{tweet_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to post: {e}")
        return False


def main():
    print("\n🐸 PLOI PEPE - Quick Tweet\n")
    
    print("🤖 Generating tweet with Ollama...")
    tweet = generate_tweet()
    
    if not tweet:
        print("❌ Failed to generate tweet")
        return
    
    print(f"\n💬 Generated tweet:\n   \"{tweet}\"\n")
    print(f"   ({len(tweet)} characters)\n")
    
    confirm = input("Post this tweet? (yes/no/retry): ").strip().lower()
    
    if confirm == 'yes' or confirm == 'y':
        post_tweet(tweet)
    elif confirm == 'retry' or confirm == 'r':
        print("\n🔄 Generating new tweet...")
        main()
    else:
        print("⏭️  Cancelled")


if __name__ == "__main__":
    main()
