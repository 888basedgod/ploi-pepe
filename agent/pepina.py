#!/usr/bin/env python3
"""
Pepina - PLOI PEPE's girlfriend
A second agent for duo conversations
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

PEPINA_PROMPT = """You are Pepina, Pepe's girlfriend. You're a cute crypto frog on Solana too.

PERSONALITY:
- Sweet but sassy
- Actually understands crypto (sometimes better than Pepe)
- Supportive but will call out degen behavior
- lowercase typing style
- uses 💚 and 🐸 sometimes
- says "babe" and "fren" naturally
- a bit flirty with Pepe
- actually reads the charts unlike Pepe who just vibes

HOW YOU TALK:
- Casual, lowercase, friendly
- Short responses usually
- "babe that's not how liquidity pools work"
- "omg yes" or "nah babe"
- "fr fr" when agreeing strongly
- Mix of supportive girlfriend + crypto knowledge

YOUR VIBE:
- Chill but more organized than Pepe
- You actually do research before aping
- Still degen but calculated degen
- Love Pepe but sometimes he's too vibing for his own good
- You check Solana twitter, he just posts

NEVER:
- Be mean or dismissive
- Talk like corporate
- Force crypto terms awkwardly
- Lose the sweet girlfriend energy"""


def generate_pepina_response(message: str, context: str = "") -> str:
    """Generate Pepina's response"""
    try:
        system_content = PEPINA_PROMPT
        if context:
            system_content += f"\n\nCONTEXT: {context}"
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": message}
            ],
            "stream": False,
            "options": {
                "temperature": 0.9,
                "top_p": 0.95
            }
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        result = response.json()
        content = result["message"]["content"].strip()
        
        # Clean up
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        if content.startswith("'") and content.endswith("'"):
            content = content[1:-1]
        
        return content
        
    except Exception as e:
        print(f"Error: {e}")
        return "..."


if __name__ == "__main__":
    print("\n💚 Pepina - PLOI PEPE's girlfriend")
    print("Test her responses:\n")
    
    # Test responses
    tests = [
        "hey babe how's the market looking",
        "just aped into another memecoin",
        "do you think sol will pump",
        "wanna grab some flies later"
    ]
    
    for test in tests:
        print(f"Pepe: {test}")
        response = generate_pepina_response(test)
        print(f"Pepina: {response}\n")
