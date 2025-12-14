#!/usr/bin/env python3
"""
Daily New Friend - Pepe meets a new agent every day
Generates a random character and has a conversation
"""

import os
import json
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
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

PEPE_PROMPT = """You are Pepe, a chill frog on Solana. You're talking to a new friend.

- laid back and chill
- curious about new people
- good listener
- lowercase, casual
- "yeah" "nice" "feels good man"
- ask questions naturally
- keep it short and conversational"""


# Agent archetypes for variety
AGENT_TEMPLATES = [
    {
        "type": "degen_trader",
        "names": ["Chad", "Dex", "Moon", "Ape", "Ser"],
        "traits": ["aggressive trader", "always looking for 100x", "degenerate gambler", "follows influencers blindly"],
        "vibe": "hyper bullish and reckless"
    },
    {
        "type": "tech_builder",
        "names": ["Dev", "Code", "Builder", "Anon", "Hacker"],
        "traits": ["building in silence", "technical genius", "hates hype", "focused on fundamentals"],
        "vibe": "serious and technical"
    },
    {
        "type": "meme_lord",
        "names": ["Jeet", "Giga", "Wojak", "Bogdanoff", "Sminem"],
        "traits": ["posts memes all day", "irony poisoned", "extremely online", "knows all the lore"],
        "vibe": "chaotic and memey"
    },
    {
        "type": "crypto_normie",
        "names": ["Mike", "Sarah", "Alex", "Jordan", "Taylor"],
        "traits": ["new to crypto", "asks basic questions", "scared of losing money", "wants to learn"],
        "vibe": "cautious and curious"
    },
    {
        "type": "whale",
        "names": ["Rex", "Titan", "Mega", "Ultra", "Apex"],
        "traits": ["moves markets", "calm and calculated", "doesn't care about small pumps", "long-term vision"],
        "vibe": "wealthy and unbothered"
    },
    {
        "type": "philosopher",
        "names": ["Sage", "Zen", "Theory", "Mind", "Soul"],
        "traits": ["deep thoughts on crypto", "sees big picture", "questions everything", "spiritual approach"],
        "vibe": "wise and contemplative"
    },
    {
        "type": "shitposter",
        "names": ["Chaos", "Rekt", "Pump", "Dump", "Gm"],
        "traits": ["lives for the chaos", "no strategy", "pure vibes", "embraces the absurd"],
        "vibe": "chaotic neutral energy"
    }
]


def generate_new_agent():
    """Generate a random new agent personality"""
    template = random.choice(AGENT_TEMPLATES)
    
    name = random.choice(template["names"])
    trait = random.choice(template["traits"])
    
    agent = {
        "name": name,
        "type": template["type"],
        "trait": trait,
        "vibe": template["vibe"],
        "created": datetime.now().strftime("%Y-%m-%d"),
        "prompt": f"""You are {name}, a {template["type"]} on Solana crypto twitter.

YOUR VIBE: {template["vibe"]}
YOUR TRAIT: {trait}

HOW YOU TALK:
- lowercase and casual
- keep responses SHORT (under 200 chars)
- stay in character
- be natural and conversational
- show your personality through your words

Remember: You're {name}, and you're {trait}. Act like it."""
    }
    
    return agent


def save_agent(agent):
    """Save agent to daily friends log"""
    os.makedirs("./data/friends", exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"./data/friends/{date_str}_{agent['name']}.json"
    
    with open(filename, 'w') as f:
        json.dump(agent, f, indent=2)
    
    return filename


def generate_response(character: str, prompt: str, message: str, history: list) -> str:
    """Generate response for a character"""
    try:
        messages = [{"role": "system", "content": prompt}]
        
        # Add conversation history (last 6 messages)
        for msg in history[-6:]:
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


def print_message(speaker: str, text: str, color: str):
    """Pretty print message"""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {speaker}:{Colors.ENDC} {text}")


def have_conversation(agent, num_exchanges=10):
    """Have a conversation between Pepe and the new agent"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}🐸 PEPE meets {agent['name'].upper()} ({agent['type']}) 💬{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    history = []
    
    # Pepe starts with a greeting
    greetings = [
        f"hey {agent['name']}, what's good fren",
        f"yo {agent['name']}, how u doing",
        f"gm {agent['name']}",
        f"hey {agent['name']}, just vibing. wbu",
        f"sup {agent['name']}, what you been up to"
    ]
    
    starter = random.choice(greetings)
    print_message("Pepe", starter, Colors.GREEN)
    history.append({"speaker": "Pepe", "text": starter})
    
    # Conversation loop
    for i in range(num_exchanges):
        # Agent responds
        agent_response = generate_response(agent["name"], agent["prompt"], history[-1]["text"], history)
        print_message(agent["name"], agent_response, Colors.BLUE)
        history.append({"speaker": agent["name"], "text": agent_response})
        
        # Pepe responds
        pepe_response = generate_response("Pepe", PEPE_PROMPT, history[-1]["text"], history)
        print_message("Pepe", pepe_response, Colors.GREEN)
        history.append({"speaker": "Pepe", "text": pepe_response})
    
    # Save conversation
    os.makedirs("./data/conversations/friends", exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_file = f"./data/conversations/friends/pepe_{agent['name']}_{date_str}.txt"
    
    with open(conv_file, 'w') as f:
        f.write(f"Pepe meets {agent['name']}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Type: {agent['type']}\n")
        f.write(f"Trait: {agent['trait']}\n")
        f.write("="*60 + "\n\n")
        for msg in history:
            f.write(f"{msg['speaker']}: {msg['text']}\n\n")
    
    print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.GREEN}✅ Conversation saved to {conv_file}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    return history


def main():
    """Main function"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}🐸 DAILY NEW FRIEND GENERATOR{Colors.ENDC}\n")
    
    # Generate new agent
    print(f"{Colors.YELLOW}🎲 Generating today's new friend...{Colors.ENDC}\n")
    agent = generate_new_agent()
    
    print(f"{Colors.BOLD}Name:{Colors.ENDC} {agent['name']}")
    print(f"{Colors.BOLD}Type:{Colors.ENDC} {agent['type']}")
    print(f"{Colors.BOLD}Trait:{Colors.ENDC} {agent['trait']}")
    print(f"{Colors.BOLD}Vibe:{Colors.ENDC} {agent['vibe']}\n")
    
    # Save agent
    agent_file = save_agent(agent)
    print(f"{Colors.GREEN}✅ Agent saved to {agent_file}{Colors.ENDC}\n")
    
    # Ask if user wants to start conversation
    start = input(f"{Colors.YELLOW}Start conversation? (yes/no): {Colors.ENDC}").strip().lower()
    
    if start in ['yes', 'y']:
        num = input(f"{Colors.YELLOW}How many exchanges? (default 10): {Colors.ENDC}").strip()
        num_exchanges = int(num) if num.isdigit() else 10
        
        have_conversation(agent, num_exchanges)
    else:
        print(f"\n{Colors.YELLOW}Agent created! Run again to meet them.{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
