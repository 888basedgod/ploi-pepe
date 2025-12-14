#!/usr/bin/env python3
"""
Pepe & Pepina Conversation Generator
Let the two agents talk to each other
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

# Colors
class Colors:
    GREEN = '\033[92m'
    PINK = '\033[95m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

PEPE_PROMPT = """You are Pepe, a chill frog on Solana. You're talking to your girlfriend Pepina.

- laid back and chill
- not the smartest with crypto tbh
- vibes over research
- love Pepina but she's smarter than you
- lowercase, casual
- "idk babe" "yeah" "feels good"
- sometimes say dumb things
- just here for the vibes"""

PEPINA_PROMPT = """You are Pepina, Pepe's girlfriend. Both crypto frogs on Solana.

- sweet but sassy
- actually understands crypto
- supportive but calls out degen behavior  
- lowercase, cute, uses 💚 sometimes
- "babe" naturally
- a bit flirty
- checks charts unlike Pepe"""


def generate_response(character: str, message: str, history: list) -> str:
    """Generate response for a character"""
    try:
        system_prompt = PEPE_PROMPT if character == "Pepe" else PEPINA_PROMPT
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in history[-6:]:  # Last 3 exchanges
            role = "assistant" if msg["speaker"] == character else "user"
            messages.append({"role": role, "content": msg["text"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.9, "top_p": 0.95}
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        result = response.json()
        content = result["message"]["content"].strip().strip('"').strip("'")
        
        # Keep it short
        if len(content) > 200:
            content = content[:197] + "..."
        
        return content
        
    except Exception as e:
        return "..."


def print_message(speaker: str, text: str):
    """Pretty print message"""
    color = Colors.GREEN if speaker == "Pepe" else Colors.PINK
    print(f"{color}{speaker}:{Colors.ENDC} {text}")


def main():
    """Run conversation"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}🐸 PEPE & PEPINA CONVERSATION 💚{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    # Conversation topics
    topics = [
        "hey babe what you up to",
        "just checking the charts",
        "thinking about that new memecoin",
        "wanna grab some flies later",
        "sol looking kinda good today",
        "probably gonna ape into something dumb",
        "what do you think about that new dex",
        "feels good man",
        "you see that pump earlier"
    ]
    
    history = []
    
    # Automated conversation
    import random
    
    # Pepe starts
    starter = random.choice(topics)
    print_message("Pepe", starter)
    history.append({"speaker": "Pepe", "text": starter})
    time.sleep(1)
    
    # 5 exchanges
    for i in range(5):
        # Pepina responds
        print(f"\n{Colors.YELLOW}[Generating response...]{Colors.ENDC}")
        pepina_response = generate_response("Pepina", history[-1]["text"], history)
        print_message("Pepina", pepina_response)
        history.append({"speaker": "Pepina", "text": pepina_response})
        time.sleep(2)
        
        # Pepe responds
        print(f"\n{Colors.YELLOW}[Generating response...]{Colors.ENDC}")
        pepe_response = generate_response("Pepe", history[-1]["text"], history)
        print_message("Pepe", pepe_response)
        history.append({"speaker": "Pepe", "text": pepe_response})
        time.sleep(2)
    
    print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.GREEN}Conversation complete! 🐸💚{Colors.ENDC}\n")
    
    # Ask to save
    save = input("Save this conversation? (yes/no): ").strip().lower()
    if save == 'yes' or save == 'y':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./data/conversations/pepe_pepina_{timestamp}.txt"
        
        os.makedirs("./data/conversations", exist_ok=True)
        
        with open(filename, 'w') as f:
            for msg in history:
                f.write(f"{msg['speaker']}: {msg['text']}\n")
        
        print(f"✅ Saved to {filename}")


if __name__ == "__main__":
    main()
