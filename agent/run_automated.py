#!/usr/bin/env python3
"""
Run PLOI Pepe with full automation
- Auto-posts to Twitter every hour
- Responds to mentions automatically
- Runs 24/7
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Import agent components
from orchestrator import Orchestrator
from platforms import TwitterAdapter
from memory import MemoryStore

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_automated.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def generate_tweet(agent) -> str:
    """Generate an autonomous tweet"""
    prompts = [
        "generate a degen crypto tweet",
        "say something about memecoins",
        "share your thoughts on solana",
        "make a joke about defi",
        "post about pump.fun",
        "comment on the current market"
    ]
    
    import random
    prompt = random.choice(prompts)
    
    response = await agent.generate_async(prompt)
    return response[:280]  # Twitter character limit


async def auto_post_task(twitter_adapter, agent):
    """Autonomous posting task"""
    try:
        tweet = await generate_tweet(agent)
        await twitter_adapter.send_message("timeline", tweet)
        logger.info(f"Auto-posted: {tweet}")
    except Exception as e:
        logger.error(f"Auto-post failed: {e}")


async def check_mentions_task(twitter_adapter, agent):
    """Check and respond to mentions"""
    try:
        mentions = await twitter_adapter.get_mentions()
        for mention in mentions:
            # Generate response
            prompt = f"Reply to this tweet: {mention['text']}"
            response = await agent.generate_async(prompt)
            
            # Post reply
            await twitter_adapter.send_message(
                mention['id'],
                response[:280],
                reply_to=mention['id']
            )
            logger.info(f"Replied to @{mention['username']}")
    except Exception as e:
        logger.error(f"Check mentions failed: {e}")


async def main():
    """Main automation loop"""
    logger.info("="*60)
    logger.info("🐸 PLOI Pepe - Autonomous Mode")
    logger.info("="*60)
    
    # Check for Together API key
    together_key = os.getenv("TOGETHER_API_KEY")
    if not together_key:
        logger.error("TOGETHER_API_KEY not set!")
        logger.error("Get one at: https://api.together.xyz/")
        logger.error("Then add it to .env file")
        return
    
    # Check Twitter credentials
    twitter_key = os.getenv("TWITTER_API_KEY")
    if not twitter_key:
        logger.warning("Twitter credentials not set. Automation disabled.")
        logger.warning("Add credentials to .env to enable Twitter posting")
        return
    
    # Initialize components
    logger.info("Initializing agent...")
    
    # Import agent (needs Together API)
    try:
        from core import PloiPepe
        agent = PloiPepe()
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return
    
    memory = MemoryStore()
    twitter = TwitterAdapter(agent, memory)
    orchestrator = Orchestrator(agent, memory)
    
    # Setup tasks
    orchestrator.add_task(
        "auto_post",
        lambda: auto_post_task(twitter, agent),
        interval_seconds=3600,  # Every hour
        enabled=True
    )
    
    orchestrator.add_task(
        "check_mentions",
        lambda: check_mentions_task(twitter, agent),
        interval_seconds=300,  # Every 5 minutes
        enabled=True
    )
    
    orchestrator.add_task(
        "save_memory",
        lambda: memory.save(),
        interval_seconds=600,  # Every 10 minutes
        enabled=True
    )
    
    logger.info("✅ Automation enabled:")
    logger.info("  - Auto-posting every hour")
    logger.info("  - Checking mentions every 5 minutes")
    logger.info("  - Saving memory every 10 minutes")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    
    # Start orchestrator
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down...")
        memory.save()
        logger.info("Memory saved. Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
