"""
Memory and Context Management
Handles conversation history, context storage, and retrieval
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Manages conversation history and context for the agent.
    Supports multi-conversation tracking and persistence.
    """
    
    def __init__(self, storage_path: str = "./data/memory.json", max_history: int = 20):
        """
        Initialize memory store.
        
        Args:
            storage_path: Path to JSON file for persistent storage
            max_history: Maximum conversation turns to keep per conversation
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Load existing memory if available
        self.load()
        
        logger.info(f"MemoryStore initialized (storage: {storage_path})")
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        Add a message to conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (timestamp, platform, etc.)
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[conversation_id].append(message)
        
        # Trim if exceeds max_history
        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_history:]
        
        logger.debug(f"Added message to conversation {conversation_id}")
    
    def get_history(
        self,
        conversation_id: str,
        format_for_model: bool = True,
        last_n: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve conversation history.
        
        Args:
            conversation_id: Conversation to retrieve
            format_for_model: If True, return in model format (role/content only)
            last_n: Only return last N messages
        
        Returns:
            List of conversation messages
        """
        if conversation_id not in self.conversations:
            return []
        
        history = self.conversations[conversation_id]
        
        if last_n:
            history = history[-last_n:]
        
        if format_for_model:
            # Return only role and content for model input
            return [{"role": msg["role"], "content": msg["content"]} for msg in history]
        
        return history
    
    def clear_conversation(self, conversation_id: str):
        """Clear a specific conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")
    
    def clear_all(self):
        """Clear all conversations"""
        self.conversations = {}
        logger.info("Cleared all conversations")
    
    def save(self):
        """Persist memory to disk"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.conversations, f, indent=2)
            logger.debug("Memory saved to disk")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def load(self):
        """Load memory from disk"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.conversations = json.load(f)
                logger.info(f"Loaded {len(self.conversations)} conversations from disk")
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
                self.conversations = {}
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        total_messages = sum(len(conv) for conv in self.conversations.values())
        return {
            "total_conversations": len(self.conversations),
            "total_messages": total_messages,
            "conversations": {
                cid: len(msgs) for cid, msgs in self.conversations.items()
            }
        }


class ContextManager:
    """
    Manages contextual information for agent responses.
    Stores facts, preferences, and platform-specific context.
    """
    
    def __init__(self, context_path: str = "./data/context.json"):
        """Initialize context manager"""
        self.context_path = Path(context_path)
        self.context_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.context = {
            "user_preferences": {},
            "platform_contexts": {},
            "knowledge_base": {}
        }
        
        self.load()
        logger.info("ContextManager initialized")
    
    def set_user_preference(self, user_id: str, key: str, value: any):
        """Store a user preference"""
        if user_id not in self.context["user_preferences"]:
            self.context["user_preferences"][user_id] = {}
        self.context["user_preferences"][user_id][key] = value
    
    def get_user_preference(self, user_id: str, key: str, default=None):
        """Retrieve a user preference"""
        return self.context["user_preferences"].get(user_id, {}).get(key, default)
    
    def set_platform_context(self, platform: str, key: str, value: any):
        """Store platform-specific context"""
        if platform not in self.context["platform_contexts"]:
            self.context["platform_contexts"][platform] = {}
        self.context["platform_contexts"][platform][key] = value
    
    def get_platform_context(self, platform: str, key: str, default=None):
        """Retrieve platform-specific context"""
        return self.context["platform_contexts"].get(platform, {}).get(key, default)
    
    def add_knowledge(self, category: str, key: str, value: any):
        """Add to knowledge base"""
        if category not in self.context["knowledge_base"]:
            self.context["knowledge_base"][category] = {}
        self.context["knowledge_base"][category][key] = value
    
    def get_knowledge(self, category: str, key: str, default=None):
        """Retrieve from knowledge base"""
        return self.context["knowledge_base"].get(category, {}).get(key, default)
    
    def save(self):
        """Persist context to disk"""
        try:
            with open(self.context_path, 'w') as f:
                json.dump(self.context, f, indent=2)
            logger.debug("Context saved to disk")
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
    
    def load(self):
        """Load context from disk"""
        if self.context_path.exists():
            try:
                with open(self.context_path, 'r') as f:
                    self.context = json.load(f)
                logger.info("Context loaded from disk")
            except Exception as e:
                logger.error(f"Failed to load context: {e}")


if __name__ == "__main__":
    # Test memory store
    memory = MemoryStore(storage_path="./test_memory.json")
    
    memory.add_message("test_conv_1", "user", "hey what's up")
    memory.add_message("test_conv_1", "assistant", "not much just vibing")
    memory.add_message("test_conv_1", "user", "thoughts on btc?")
    
    print(memory.get_history("test_conv_1"))
    print(memory.get_stats())
