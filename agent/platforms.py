"""
Platform Integrations
Adapters for Twitter, Discord, Telegram, and other platforms
"""

import os
import logging
from typing import Optional, Dict, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class PlatformAdapter(ABC):
    """Base class for platform integrations"""
    
    def __init__(self, agent, memory_store):
        self.agent = agent
        self.memory = memory_store
        self.platform_name = "unknown"
    
    @abstractmethod
    async def send_message(self, conversation_id: str, message: str, **kwargs):
        """Send a message on the platform"""
        pass
    
    @abstractmethod
    async def listen(self, callback: Callable):
        """Listen for incoming messages"""
        pass
    
    @abstractmethod
    async def get_mentions(self) -> list:
        """Get mentions/notifications"""
        pass


class TwitterAdapter(PlatformAdapter):
    """
    Twitter/X integration adapter.
    Requires tweepy library and Twitter API credentials.
    """
    
    def __init__(self, agent, memory_store, api_key: str = None, api_secret: str = None,
                 access_token: str = None, access_token_secret: str = None, bearer_token: str = None):
        super().__init__(agent, memory_store)
        self.platform_name = "twitter"
        
        # Load credentials from env if not provided
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
        
        self.client = None
        self._setup_client()
        
        logger.info("TwitterAdapter initialized")
    
    def _setup_client(self):
        """Initialize Twitter API client"""
        try:
            import tweepy
            
            # OAuth 1.0a authentication for posting
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            
            # API v2 client
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            
            logger.info("Twitter API client initialized")
            
        except ImportError:
            logger.error("tweepy not installed. Run: pip install tweepy")
            raise
        except Exception as e:
            logger.error(f"Failed to setup Twitter client: {e}")
            raise
    
    async def send_message(self, conversation_id: str, message: str, **kwargs):
        """
        Post a tweet or reply.
        
        Args:
            conversation_id: Tweet ID to reply to (None for new tweet)
            message: Tweet text
            **kwargs: Additional Twitter API parameters
        """
        try:
            if conversation_id and conversation_id != "timeline":
                # Reply to a tweet
                response = self.client.create_tweet(
                    text=message,
                    in_reply_to_tweet_id=conversation_id,
                    **kwargs
                )
            else:
                # New tweet
                response = self.client.create_tweet(text=message, **kwargs)
            
            tweet_id = response.data['id']
            logger.info(f"Posted tweet: {tweet_id}")
            
            # Store in memory
            self.memory.add_message(
                conversation_id or "timeline",
                "assistant",
                message,
                {"platform": "twitter", "tweet_id": tweet_id}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            raise
    
    async def get_mentions(self) -> list:
        """Get recent mentions"""
        try:
            # Get authenticated user ID
            me = self.client.get_me()
            user_id = me.data.id
            
            # Get mentions
            mentions = self.client.get_users_mentions(
                user_id,
                max_results=10,
                tweet_fields=['created_at', 'conversation_id', 'author_id']
            )
            
            return mentions.data if mentions.data else []
            
        except Exception as e:
            logger.error(f"Failed to get mentions: {e}")
            return []
    
    async def listen(self, callback: Callable):
        """
        Listen for mentions and trigger callback.
        Note: This is a polling implementation. For real-time,
        consider using Twitter Streaming API.
        """
        import asyncio
        
        logger.info("Starting Twitter listener (polling mode)")
        last_mention_id = None
        
        while True:
            try:
                mentions = await self.get_mentions()
                
                for mention in mentions:
                    # Skip if already processed
                    if last_mention_id and mention.id <= last_mention_id:
                        continue
                    
                    # Process mention
                    context = {
                        "platform": "twitter",
                        "tweet_id": mention.id,
                        "conversation_id": mention.conversation_id,
                        "author_id": mention.author_id,
                        "is_mention": True
                    }
                    
                    await callback(mention.text, context)
                    
                    last_mention_id = max(last_mention_id or 0, mention.id)
                
                # Poll every 60 seconds (respect rate limits)
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in Twitter listener: {e}")
                await asyncio.sleep(60)


class DiscordAdapter(PlatformAdapter):
    """
    Discord integration adapter.
    Requires discord.py library and bot token.
    """
    
    def __init__(self, agent, memory_store, bot_token: str = None):
        super().__init__(agent, memory_store)
        self.platform_name = "discord"
        
        self.bot_token = bot_token or os.getenv("DISCORD_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("DISCORD_BOT_TOKEN not set")
        
        self.client = None
        logger.info("DiscordAdapter initialized")
    
    async def setup(self):
        """Initialize Discord client"""
        try:
            import discord
            from discord.ext import commands
            
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            
            self.client = commands.Bot(command_prefix='!', intents=intents)
            
            @self.client.event
            async def on_ready():
                logger.info(f"Discord bot logged in as {self.client.user}")
            
            logger.info("Discord client initialized")
            
        except ImportError:
            logger.error("discord.py not installed. Run: pip install discord.py")
            raise
    
    async def send_message(self, conversation_id: str, message: str, **kwargs):
        """
        Send a Discord message.
        
        Args:
            conversation_id: Channel ID
            message: Message text
        """
        try:
            channel = self.client.get_channel(int(conversation_id))
            if not channel:
                raise ValueError(f"Channel {conversation_id} not found")
            
            sent_message = await channel.send(message)
            
            # Store in memory
            self.memory.add_message(
                conversation_id,
                "assistant",
                message,
                {"platform": "discord", "message_id": sent_message.id}
            )
            
            logger.info(f"Sent Discord message to channel {conversation_id}")
            return sent_message
            
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            raise
    
    async def listen(self, callback: Callable):
        """Listen for Discord messages"""
        
        @self.client.event
        async def on_message(message):
            # Ignore own messages
            if message.author == self.client.user:
                return
            
            # Check if bot was mentioned
            is_mention = self.client.user in message.mentions
            
            context = {
                "platform": "discord",
                "channel_id": str(message.channel.id),
                "author_id": str(message.author.id),
                "author_name": message.author.name,
                "is_mention": is_mention,
                "message_id": message.id
            }
            
            # Call the callback
            await callback(message.content, context)
        
        # Start bot
        await self.client.start(self.bot_token)
    
    async def get_mentions(self) -> list:
        """Get recent mentions (not implemented for Discord)"""
        # Discord provides mentions in the on_message event
        return []


class TelegramAdapter(PlatformAdapter):
    """
    Telegram integration adapter.
    Requires python-telegram-bot library.
    """
    
    def __init__(self, agent, memory_store, bot_token: str = None):
        super().__init__(agent, memory_store)
        self.platform_name = "telegram"
        
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        
        self.application = None
        logger.info("TelegramAdapter initialized")
    
    async def setup(self):
        """Initialize Telegram bot"""
        try:
            from telegram.ext import Application
            
            self.application = Application.builder().token(self.bot_token).build()
            logger.info("Telegram bot initialized")
            
        except ImportError:
            logger.error("python-telegram-bot not installed. Run: pip install python-telegram-bot")
            raise
    
    async def send_message(self, conversation_id: str, message: str, **kwargs):
        """
        Send a Telegram message.
        
        Args:
            conversation_id: Chat ID
            message: Message text
        """
        try:
            await self.application.bot.send_message(
                chat_id=conversation_id,
                text=message,
                **kwargs
            )
            
            # Store in memory
            self.memory.add_message(
                conversation_id,
                "assistant",
                message,
                {"platform": "telegram"}
            )
            
            logger.info(f"Sent Telegram message to chat {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            raise
    
    async def listen(self, callback: Callable):
        """Listen for Telegram messages"""
        from telegram.ext import MessageHandler, filters
        
        async def message_handler(update, context):
            message = update.message
            
            ctx = {
                "platform": "telegram",
                "chat_id": str(message.chat_id),
                "user_id": str(message.from_user.id),
                "username": message.from_user.username,
                "is_mention": True  # Direct messages
            }
            
            await callback(message.text, ctx)
        
        # Add handler
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        
        # Start bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
    
    async def get_mentions(self) -> list:
        """Get recent mentions (not applicable for Telegram)"""
        return []


# Export adapters
__all__ = [
    'PlatformAdapter',
    'TwitterAdapter',
    'DiscordAdapter',
    'TelegramAdapter'
]
