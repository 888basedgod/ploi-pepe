#!/usr/bin/env python3
"""
Demo script showing PLOI Pepe conversations
Simulates interactions and displays in terminal
"""

import os
import sys
import time
from dotenv import load_dotenv
from core import PloiPepe

# Load environment
load_dotenv()

# Colors
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_conversation(user_msg: str, pepe_response: str):
    """Print a conversation exchange"""
    print(f"{Colors.BLUE}User:{Colors.ENDC} {user_msg}")
    print(f"{Colors.GREEN}Pepe:{Colors.ENDC} {pepe_response}")
    print()
    time.sleep(1)

def main():
    """Run demo conversations"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.GREEN}🐸 PLOI Pepe Demo{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    if not os.getenv("TOGETHER_API_KEY"):
        print(f"{Colors.YELLOW}Set TOGETHER_API_KEY in .env to run this demo{Colors.ENDC}\n")
        sys.exit(1)
    
    # Initialize
    print(f"{Colors.YELLOW}Initializing Pepe...{Colors.ENDC}\n")
    pepe = PloiPepe()
    
    # Demo conversations
    demo_prompts = [
        "gm",
        "what do you think about solana?",
        "any hot takes on the market?",
        "thoughts on memecoins?",
        "what keeps you up at night?",
    ]
    
    print(f"{Colors.BOLD}Demo Conversations:{Colors.ENDC}\n")
    
    for prompt in demo_prompts:
        print(f"{Colors.CYAN}>{Colors.ENDC} Asking: {prompt}")
        response = pepe.generate(prompt)
        print_conversation(prompt, response)
    
    print(f"{Colors.GREEN}Demo complete!{Colors.ENDC}")
    print(f"{Colors.CYAN}Run 'python chat.py' for interactive mode{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
