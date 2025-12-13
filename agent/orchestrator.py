"""
Agent Orchestrator
Handles scheduling, triggers, and autonomous behavior
"""

import logging
import asyncio
import random
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Scheduled task configuration"""
    name: str
    callback: Callable
    interval_seconds: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    run_count: int = 0


class Orchestrator:
    """
    Manages agent scheduling and autonomous behavior.
    Handles periodic tasks, event triggers, and activity patterns.
    """
    
    def __init__(self, agent, memory_store, variance_factor: float = 0.2):
        """
        Initialize orchestrator.
        
        Args:
            agent: PloiPepe instance
            memory_store: MemoryStore instance
            variance_factor: Randomness in scheduling (0.0-1.0)
        """
        self.agent = agent
        self.memory = memory_store
        self.variance_factor = variance_factor
        
        self.tasks: List[Task] = []
        self.running = False
        
        logger.info("Orchestrator initialized")
    
    def add_task(
        self,
        name: str,
        callback: Callable,
        interval_seconds: int,
        enabled: bool = True
    ):
        """
        Add a scheduled task.
        
        Args:
            name: Task identifier
            callback: Function to execute (async)
            interval_seconds: Base interval between executions
            enabled: Whether task is active
        """
        task = Task(
            name=name,
            callback=callback,
            interval_seconds=interval_seconds,
            enabled=enabled
        )
        self.tasks.append(task)
        logger.info(f"Added task: {name} (interval: {interval_seconds}s)")
    
    def remove_task(self, name: str):
        """Remove a task by name"""
        self.tasks = [t for t in self.tasks if t.name != name]
        logger.info(f"Removed task: {name}")
    
    def enable_task(self, name: str):
        """Enable a task"""
        for task in self.tasks:
            if task.name == name:
                task.enabled = True
                logger.info(f"Enabled task: {name}")
    
    def disable_task(self, name: str):
        """Disable a task"""
        for task in self.tasks:
            if task.name == name:
                task.enabled = False
                logger.info(f"Disabled task: {name}")
    
    def _calculate_next_run(self, task: Task) -> float:
        """
        Calculate next run time with variance.
        Adds randomness to avoid predictable patterns.
        """
        base_interval = task.interval_seconds
        variance = base_interval * self.variance_factor
        
        # Random adjustment within variance range
        adjustment = random.uniform(-variance, variance)
        next_interval = base_interval + adjustment
        
        return max(1.0, next_interval)  # Minimum 1 second
    
    async def _run_task(self, task: Task):
        """Execute a single task"""
        try:
            logger.info(f"Executing task: {task.name}")
            
            # Call the task callback
            if asyncio.iscoroutinefunction(task.callback):
                await task.callback()
            else:
                task.callback()
            
            task.last_run = datetime.now()
            task.run_count += 1
            
            logger.info(f"Task {task.name} completed (runs: {task.run_count})")
            
        except Exception as e:
            logger.error(f"Task {task.name} failed: {e}")
    
    async def _task_loop(self, task: Task):
        """Run a task in a loop"""
        while self.running:
            if task.enabled:
                await self._run_task(task)
            
            # Calculate next run time with variance
            next_run = self._calculate_next_run(task)
            logger.debug(f"Task {task.name} next run in {next_run:.1f}s")
            
            await asyncio.sleep(next_run)
    
    async def start(self):
        """Start the orchestrator"""
        if self.running:
            logger.warning("Orchestrator already running")
            return
        
        self.running = True
        logger.info("Starting orchestrator...")
        
        # Create task loops
        task_loops = [self._task_loop(task) for task in self.tasks]
        
        try:
            # Run all tasks concurrently
            await asyncio.gather(*task_loops)
        except asyncio.CancelledError:
            logger.info("Orchestrator cancelled")
        finally:
            self.running = False
    
    def stop(self):
        """Stop the orchestrator"""
        logger.info("Stopping orchestrator...")
        self.running = False
    
    def get_status(self) -> Dict:
        """Get orchestrator status"""
        return {
            "running": self.running,
            "tasks": [
                {
                    "name": t.name,
                    "enabled": t.enabled,
                    "interval": t.interval_seconds,
                    "last_run": t.last_run.isoformat() if t.last_run else None,
                    "run_count": t.run_count
                }
                for t in self.tasks
            ]
        }


class TriggerManager:
    """
    Manages event-based triggers for agent responses.
    Handles mentions, keywords, DMs, etc.
    """
    
    def __init__(self, agent, memory_store):
        """Initialize trigger manager"""
        self.agent = agent
        self.memory = memory_store
        
        self.triggers = []
        
        logger.info("TriggerManager initialized")
    
    def add_keyword_trigger(
        self,
        keywords: List[str],
        callback: Callable,
        case_sensitive: bool = False
    ):
        """
        Add a keyword-based trigger.
        
        Args:
            keywords: List of keywords to watch for
            callback: Function to call when triggered
            case_sensitive: Whether matching is case-sensitive
        """
        trigger = {
            "type": "keyword",
            "keywords": keywords if case_sensitive else [k.lower() for k in keywords],
            "case_sensitive": case_sensitive,
            "callback": callback
        }
        self.triggers.append(trigger)
        logger.info(f"Added keyword trigger: {keywords}")
    
    def add_mention_trigger(self, callback: Callable):
        """Add a trigger for @mentions"""
        trigger = {
            "type": "mention",
            "callback": callback
        }
        self.triggers.append(trigger)
        logger.info("Added mention trigger")
    
    async def check_triggers(self, message: str, context: Dict) -> bool:
        """
        Check if message triggers any responses.
        
        Args:
            message: Incoming message text
            context: Additional context (platform, user, etc.)
        
        Returns:
            True if any trigger was activated
        """
        triggered = False
        
        for trigger in self.triggers:
            if trigger["type"] == "keyword":
                text = message if trigger["case_sensitive"] else message.lower()
                
                for keyword in trigger["keywords"]:
                    if keyword in text:
                        logger.info(f"Keyword trigger activated: {keyword}")
                        
                        if asyncio.iscoroutinefunction(trigger["callback"]):
                            await trigger["callback"](message, context)
                        else:
                            trigger["callback"](message, context)
                        
                        triggered = True
            
            elif trigger["type"] == "mention":
                # Platform-specific mention detection
                if context.get("is_mention", False):
                    logger.info("Mention trigger activated")
                    
                    if asyncio.iscoroutinefunction(trigger["callback"]):
                        await trigger["callback"](message, context)
                    else:
                        trigger["callback"](message, context)
                    
                    triggered = True
        
        return triggered


if __name__ == "__main__":
    # Test example
    from core import PloiPepe
    from memory import MemoryStore
    
    agent = PloiPepe()
    memory = MemoryStore()
    orch = Orchestrator(agent, memory)
    
    async def test_task():
        print(f"[{datetime.now()}] Test task executed")
    
    orch.add_task("test", test_task, interval_seconds=5)
    
    print("Starting orchestrator (Ctrl+C to stop)")
    try:
        asyncio.run(orch.start())
    except KeyboardInterrupt:
        print("\nStopped")
