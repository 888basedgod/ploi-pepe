"""
PLOI Pepe - Local Inference Core
Run the model locally without Together API
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PloiPepeLocal:
    """
    PLOI Pepe running locally with transformers.
    Loads lh-degen-001 adapter and base model.
    """
    
    def __init__(
        self,
        adapter_path: str = "../lh-degen-001",
        system_prompt: Optional[str] = None,
        temperature: float = 0.9,
        top_p: float = 0.95,
        repetition_penalty: float = 1.1,
        max_tokens: int = 256,
        device: str = "auto"
    ):
        """
        Initialize local model.
        
        Args:
            adapter_path: Path to lh-degen-001 adapter
            system_prompt: Custom system prompt
            temperature: Sampling temperature
            top_p: Nucleus sampling
            repetition_penalty: Prevents repetition
            max_tokens: Max response length
            device: Device to use ('auto', 'cpu', 'cuda', 'mps')
        """
        self.adapter_path = Path(adapter_path)
        
        if not self.adapter_path.exists():
            raise ValueError(f"Adapter not found at {adapter_path}")
        
        # Default system prompt
        self.system_prompt = system_prompt or (
            "you're an anonymous user on 4chan /biz/ and crypto twitter. "
            "casual, direct, unfiltered. no corporate speak."
        )
        
        # Generation parameters
        self.temperature = temperature
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.max_tokens = max_tokens
        self.device = device
        
        # Load model
        self.model = None
        self.tokenizer = None
        self._load_model()
        
        logger.info(f"PLOI Pepe (local) initialized")
    
    def _load_model(self):
        """Load model and tokenizer"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            from peft import PeftModel
            import torch
            
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.adapter_path))
            
            logger.info("Loading base model (this may take a while)...")
            logger.info("Note: Requires Llama-4-Scout-17B-16E base model")
            
            # Try to load base model
            base_model_name = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
            
            try:
                base_model = AutoModelForCausalLM.from_pretrained(
                    base_model_name,
                    device_map=self.device,
                    torch_dtype=torch.bfloat16,
                    trust_remote_code=True
                )
            except Exception as e:
                logger.error(f"Failed to load base model: {e}")
                logger.error("You need access to meta-llama/Llama-4-Scout-17B-16E-Instruct")
                logger.error("Alternative: Use Together API (see core.py)")
                raise
            
            logger.info("Loading LoRA adapter...")
            self.model = PeftModel.from_pretrained(base_model, str(self.adapter_path))
            
            logger.info("Model loaded successfully!")
            
        except ImportError as e:
            logger.error("Missing dependencies. Install with:")
            logger.error("pip install transformers peft torch accelerate")
            raise
    
    def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """
        Generate a response.
        
        Args:
            prompt: User message
            conversation_history: Previous turns
            **kwargs: Override generation parameters
        
        Returns:
            Generated response
        """
        # Build messages
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": prompt})
        
        # Apply chat template
        input_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        inputs = self.tokenizer(input_text, return_tensors="pt")
        
        if self.device != "cpu":
            inputs = inputs.to(self.model.device)
        
        # Generation parameters
        gen_params = {
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
            "repetition_penalty": kwargs.get("repetition_penalty", self.repetition_penalty),
            "max_new_tokens": kwargs.get("max_tokens", self.max_tokens),
            "do_sample": True,
            "pad_token_id": self.tokenizer.eos_token_id
        }
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(**inputs, **gen_params)
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the assistant response
        # (remove the prompt and system parts)
        if "assistant" in response.lower():
            parts = response.split("assistant", 1)
            if len(parts) > 1:
                response = parts[1].strip()
        
        logger.info(f"Generated response ({len(response)} chars)")
        return response


if __name__ == "__main__":
    # Quick test
    try:
        pepe = PloiPepeLocal()
        response = pepe.generate("gm")
        print(f"\nPrompt: gm")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Local inference requires:")
        print("1. Base model access (Llama-4-Scout)")
        print("2. GPU with sufficient VRAM (~40GB)")
        print("3. pip install transformers peft torch accelerate")
