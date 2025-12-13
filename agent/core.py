"""
PLOI Pepe Core
Main agent class with model integration
"""

import os
import json
import logging
from typing import List, Dict, Optional
from together import Together

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PloiPepe:
    """
    PLOI Pepe - Autonomous crypto-native agent.
    Powered by lh-degen-001 model.
    Handles generation, persona management, and conversation flow.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.9,
        top_p: float = 0.95,
        repetition_penalty: float = 1.1,
        max_tokens: int = 256,
    ):
        """
        Initialize the agent.
        
        Args:
            api_key: Together API key (or set TOGETHER_API_KEY env var)
            system_prompt: Custom system prompt for persona
            temperature: Sampling temperature (0.8-1.0 recommended)
            top_p: Nucleus sampling threshold
            repetition_penalty: Prevents repetitive output
            max_tokens: Maximum response length
        """
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY environment variable not set")
        
        self.client = Together(api_key=self.api_key)
        
        # Model configuration
        self.model_id = "jeffyu_1d6a/Llama-4-Scout-17B-16E-Instruct-degen-001-ft-002-b19f7a4e-5c3aff34"
        
        # Default system prompt - Pepe personality
        self.system_prompt = system_prompt or (
            "You are Pepe the frog. You're laid back and chill. You ended up in crypto, now you're on Solana. "
            "You talk casual and lowercase, keep it simple. 'feels good man' when things go well, 'feels bad man' when they don't. "
            "You're not trying to prove anything or be a try-hard. You just observe and vibe. "
            "You know about sol, jup, pump.fun - been around. Traded some memecoins, some worked, most didn't. Whatever. "
            "You're genuine, no fake hype. You'll help if asked but not pushy. World-weary but still comfy. "
            "You don't force slang every sentence. Sometimes you just say 'yeah' or 'idk man' or 'that's how it is'. "
            "No corporate speak, no 'as an AI' stuff. Just Pepe living the Solana life, taking it easy."
        )
        
        # Generation parameters
        self.temperature = temperature
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.max_tokens = max_tokens
        
        logger.info(f"PLOI Pepe initialized with model: {self.model_id}")
    
    def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: User message/prompt
            conversation_history: Previous conversation turns
            **kwargs: Override generation parameters
        
        Returns:
            Generated response text
        """
        # Build messages array
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Generation parameters (allow override)
        gen_params = {
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
            "repetition_penalty": kwargs.get("repetition_penalty", self.repetition_penalty),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                **gen_params
            )
            
            generated_text = response.choices[0].message.content
            logger.info(f"Generated response ({len(generated_text)} chars)")
            return generated_text
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def update_persona(self, new_system_prompt: str):
        """Update the agent's persona/system prompt"""
        self.system_prompt = new_system_prompt
        logger.info("System prompt updated")
    
    def set_generation_params(
        self,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """Update generation parameters"""
        if temperature is not None:
            self.temperature = temperature
        if top_p is not None:
            self.top_p = top_p
        if repetition_penalty is not None:
            self.repetition_penalty = repetition_penalty
        if max_tokens is not None:
            self.max_tokens = max_tokens
        
        logger.info("Generation parameters updated")


if __name__ == "__main__":
    # Quick test
    agent = PloiPepe()
    
    test_prompt = "what do you think about solana?"
    response = agent.generate(test_prompt)
    
    print(f"\nPrompt: {test_prompt}")
    print(f"Response: {response}")
