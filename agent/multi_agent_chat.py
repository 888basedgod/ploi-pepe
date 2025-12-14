#!/usr/bin/env python3
"""
Multi-Agent Continuous Conversation
Multiple agents in a group chat that runs continuously
"""

import os
import random
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

# Colors
class Colors:
    GREEN = '\033[92m'
    PINK = '\033[95m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    PURPLE = '\033[95m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Agent definitions
AGENTS = [
    {
        "name": "Pepe",
        "color": Colors.GREEN,
        "prompt": """You are Pepe, the chill frog on Solana.
- laid back and observant
- "feels good man" when vibing
- lowercase, casual
- sometimes just agrees or adds small thoughts
- good listener in group chats"""
    },
    {
        "name": "Chad",
        "color": Colors.BLUE,
        "prompt": """You are Chad, the degen trader.
- always bullish, looking for 100x
- hypes up every coin
- "ser" "gm" "wen moon"
- aggressive and confident
- shares alpha (real or not)"""
    },
    {
        "name": "Luna",
        "color": Colors.PINK,
        "prompt": """You are Luna, the smart crypto analyst.
- analytical and data-driven
- checks charts and fundamentals
- calls out bad takes politely
- actually knows what she's talking about
- skeptical but fair"""
    },
    {
        "name": "Dex",
        "color": Colors.YELLOW,
        "prompt": """You are Dex, the builder/dev.
- technical minded
- talks about protocols and tech
- less interested in price, more in innovation
- drops knowledge casually
- lowercase, brief"""
    },
    {
        "name": "Wojak",
        "color": Colors.CYAN,
        "prompt": """You are Wojak, the meme lord.
- extremely online
- makes jokes and references
- chaotic energy
- irony poisoned but lovable
- just here for the lulz"""
    }
]


def generate_response(agent: dict, history: list) -> str:
    """Generate response for an agent based on conversation history"""
    try:
        messages = [{"role": "system", "content": agent["prompt"]}]
        
        # Add recent conversation history
        for msg in history[-8:]:
            role = "assistant" if msg["speaker"] == agent["name"] else "user"
            content = f"{msg['speaker']}: {msg['text']}" if role == "user" else msg["text"]
            messages.append({"role": role, "content": content})
        
        # Context for response
        context = "Respond naturally to the group conversation. Keep it SHORT (under 200 chars). Be yourself."
        messages.append({"role": "user", "content": context})
        
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


def print_message(agent: dict, text: str):
    """Pretty print message"""
    ts = datetime.now().strftime("%H:%M:%S")
    color = agent["color"]
    print(f"{color}[{ts}] {agent['name']}:{Colors.ENDC} {text}")


def main():
    """Run continuous multi-agent conversation"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}🐸 MULTI-AGENT GROUP CHAT 💬{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.YELLOW}Press Ctrl+C to stop and save{Colors.ENDC}\n")
    
    # Show agents
    print(f"{Colors.BOLD}Agents in chat:{Colors.ENDC}")
    for agent in AGENTS:
        print(f"  {agent['color']}• {agent['name']}{Colors.ENDC}")
    print()
    
    # Starting topics
    topics = [
        "gm frens, what we thinking about sol today",
        "anyone see that new memecoin launch",
        "just got rekt on a trade lol",
        "feels like a good day to touch grass",
        "the charts looking kinda spicy ngl",
        "who's building something cool rn",
        "idk man this market is wild",
        "anyone check out that new dex",
        "solana szn incoming fr",
        "just vibing what's everyone up to"
    ]
    
    history = []
    
    # Random agent starts
    starter_agent = random.choice(AGENTS)
    starter = random.choice(topics)
    print_message(starter_agent, starter)
    history.append({"speaker": starter_agent["name"], "text": starter})
    
    try:
        exchange_count = 0
        
        while True:
            # Pick random agent to speak next (not the one who just spoke)
            available = [a for a in AGENTS if a["name"] != history[-1]["speaker"]]
            next_agent = random.choice(available)
            
            # Generate response
            response = generate_response(next_agent, history)
            print_message(next_agent, response)
            history.append({"speaker": next_agent["name"], "text": response})
            
            exchange_count += 1
            
            # Show progress every 10 messages
            if exchange_count % 10 == 0:
                print(f"\n{Colors.YELLOW}💬 {exchange_count} messages...{Colors.ENDC}\n")
            
            # Small delay between messages
            import time
            time.sleep(1.5)
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.GREEN}Conversation stopped! 🐸💬{Colors.ENDC}")
        print(f"{Colors.YELLOW}Total messages: {exchange_count}{Colors.ENDC}\n")
        
        # Ask to save
        save = input("Save this conversation? (yes/no): ").strip().lower()
        if save in ['yes', 'y']:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"./data/conversations/multiagent_{timestamp}.txt"
            
            os.makedirs("./data/conversations", exist_ok=True)
            
            with open(filename, 'w') as f:
                f.write(f"Multi-Agent Group Chat\n")
                f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total messages: {exchange_count}\n")
                f.write(f"Agents: {', '.join([a['name'] for a in AGENTS])}\n")
                f.write("="*60 + "\n\n")
                for msg in history:
                    f.write(f"{msg['speaker']}: {msg['text']}\n\n")
            
            print(f"✅ Saved to {filename}")
        
        print(f"\n{Colors.GREEN}Goodbye! 🐸{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
