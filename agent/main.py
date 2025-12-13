"""
Main entry point for lh-degen-001 agent
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import agent components
from core import PloiPepe
from memory import MemoryStore, ContextManager
from orchestrator import Orchestrator, TriggerManager
from platforms import TwitterAdapter, DiscordAdapter, TelegramAdapter

# Load environment variables
load_dotenv()

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AgentRunner:
    """Main agent runner that coordinates all components"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize agent runner"""
        self.config = self._load_config(config_path)
        
        # Initialize core components
        logger.info("Initializing agent components...")
        
        # Agent
        self.agent = PloiPepe(
            system_prompt=self.config["agent"]["persona"]["system_prompt"],
            temperature=self.config["agent"]["generation"]["temperature"],
            top_p=self.config["agent"]["generation"]["top_p"],
            repetition_penalty=self.config["agent"]["generation"]["repetition_penalty"],
            max_tokens=self.config["agent"]["generation"]["max_tokens"]
        )
        
        # Memory
        self.memory = MemoryStore(
            storage_path=self.config["memory"]["storage_path"],
            max_history=self.config["memory"]["max_history"]
        )
        
        self.context_manager = ContextManager(
            context_path=self.config["memory"]["context_path"]
        )
        
        # Orchestrator
        self.orchestrator = Orchestrator(
            self.agent,
            self.memory,
            variance_factor=self.config["orchestrator"]["schedule_variance"]
        )
        
        # Trigger manager
        self.trigger_manager = TriggerManager(self.agent, self.memory)
        
        # Platform adapters
        self.platforms = {}
        self._setup_platforms()
        
        # Setup tasks and triggers
        self._setup_orchestrator()
        self._setup_triggers()
        
        logger.info("Agent initialized successfully")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)
    
    def _setup_platforms(self):
        """Initialize platform adapters"""
        # Twitter
        if self.config["platforms"]["twitter"]["enabled"]:
            try:
                self.platforms["twitter"] = TwitterAdapter(self.agent, self.memory)
                logger.info("Twitter adapter enabled")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter adapter: {e}")
        
        # Discord
        if self.config["platforms"]["discord"]["enabled"]:
            try:
                self.platforms["discord"] = DiscordAdapter(self.agent, self.memory)
                asyncio.create_task(self.platforms["discord"].setup())
                logger.info("Discord adapter enabled")
            except Exception as e:
                logger.error(f"Failed to initialize Discord adapter: {e}")
        
        # Telegram
        if self.config["platforms"]["telegram"]["enabled"]:
            try:
                self.platforms["telegram"] = TelegramAdapter(self.agent, self.memory)
                asyncio.create_task(self.platforms["telegram"].setup())
                logger.info("Telegram adapter enabled")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram adapter: {e}")
    
    def _setup_orchestrator(self):
        """Setup scheduled tasks"""
        for task_config in self.config["orchestrator"]["tasks"]:
            if not task_config["enabled"]:
                continue
            
            task_name = task_config["name"]
            
            if task_name == "auto_post":
                self.orchestrator.add_task(
                    "auto_post",
                    self._auto_post_task,
                    task_config["interval_seconds"]
                )
            
            elif task_name == "check_mentions":
                self.orchestrator.add_task(
                    "check_mentions",
                    self._check_mentions_task,
                    task_config["interval_seconds"]
                )
            
            elif task_name == "save_memory":
                self.orchestrator.add_task(
                    "save_memory",
                    self._save_memory_task,
                    task_config["interval_seconds"]
                )
    
    def _setup_triggers(self):
        """Setup event triggers"""
        # Keyword triggers
        if self.config["triggers"]["enable_keyword_triggers"]:
            self.trigger_manager.add_keyword_trigger(
                self.config["triggers"]["keywords"],
                self._handle_keyword_trigger
            )
        
        # Mention triggers
        if self.config["triggers"]["enable_mention_triggers"]:
            self.trigger_manager.add_mention_trigger(
                self._handle_mention_trigger
            )
    
    async def _auto_post_task(self):
        """Task: Post autonomously"""
        logger.info("Executing auto-post task")
        
        # Generate a post
        prompts = [
            "share a quick thought about the crypto market",
            "what's your take on current market conditions?",
            "any hot takes?",
            "thoughts on recent price action?"
        ]
        
        import random
        prompt = random.choice(prompts)
        
        response = self.agent.generate(prompt)
        
        # Post to enabled platforms
        for platform_name, adapter in self.platforms.items():
            try:
                await adapter.send_message("timeline", response)
            except Exception as e:
                logger.error(f"Failed to post to {platform_name}: {e}")
    
    async def _check_mentions_task(self):
        """Task: Check for mentions/notifications"""
        logger.debug("Checking mentions...")
        
        for platform_name, adapter in self.platforms.items():
            try:
                mentions = await adapter.get_mentions()
                
                for mention in mentions:
                    # Process mention through trigger manager
                    context = {
                        "platform": platform_name,
                        "is_mention": True
                    }
                    await self.trigger_manager.check_triggers(mention.text, context)
                    
            except Exception as e:
                logger.error(f"Failed to check mentions on {platform_name}: {e}")
    
    async def _save_memory_task(self):
        """Task: Save memory and context to disk"""
        logger.debug("Saving memory to disk...")
        self.memory.save()
        self.context_manager.save()
    
    async def _handle_keyword_trigger(self, message: str, context: dict):
        """Handle keyword-triggered responses"""
        logger.info(f"Handling keyword trigger: {context}")
        
        # Generate response
        conversation_id = context.get("conversation_id", "default")
        history = self.memory.get_history(conversation_id, last_n=5)
        
        response = self.agent.generate(message, history)
        
        # Store in memory
        self.memory.add_message(conversation_id, "user", message, context)
        self.memory.add_message(conversation_id, "assistant", response, context)
        
        # Send response on platform
        platform = context.get("platform")
        if platform and platform in self.platforms:
            await self.platforms[platform].send_message(conversation_id, response)
    
    async def _handle_mention_trigger(self, message: str, context: dict):
        """Handle mention-triggered responses"""
        logger.info(f"Handling mention trigger: {context}")
        
        # Similar to keyword trigger
        await self._handle_keyword_trigger(message, context)
    
    async def start(self):
        """Start the agent"""
        logger.info("Starting agent...")
        
        # Start platform listeners
        listener_tasks = []
        
        for platform_name, adapter in self.platforms.items():
            async def message_callback(message, context):
                await self.trigger_manager.check_triggers(message, context)
            
            listener_tasks.append(adapter.listen(message_callback))
        
        # Start orchestrator
        orchestrator_task = self.orchestrator.start()
        
        # Run all tasks
        try:
            await asyncio.gather(orchestrator_task, *listener_tasks)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down agent...")
        
        # Stop orchestrator
        self.orchestrator.stop()
        
        # Save memory
        self.memory.save()
        self.context_manager.save()
        
        logger.info("Agent shut down successfully")


async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("PLOI Pepe - Autonomous Agent")
    logger.info("Powered by lh-degen-001")
    logger.info("=" * 60)
    
    # Check for Together API key
    if not os.getenv("TOGETHER_API_KEY"):
        logger.error("TOGETHER_API_KEY not set. Please set it in .env file")
        sys.exit(1)
    
    # Initialize and start agent
    runner = AgentRunner()
    
    try:
        await runner.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
