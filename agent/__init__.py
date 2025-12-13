"""
PLOI Pepe Agent Package
"""

from .core import PloiPepe
from .memory import MemoryStore, ContextManager
from .orchestrator import Orchestrator, TriggerManager
from .platforms import TwitterAdapter, DiscordAdapter, TelegramAdapter

__version__ = "0.1.0"
__all__ = [
    "PloiPepe",
    "MemoryStore",
    "ContextManager",
    "Orchestrator",
    "TriggerManager",
    "TwitterAdapter",
    "DiscordAdapter",
    "TelegramAdapter",
]
