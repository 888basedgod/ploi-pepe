#!/usr/bin/env python3
"""
Interactive chat terminal for PLOI Pepe
Watch conversations in real-time
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from core import PloiPepe
from memory import MemoryStore

# Load environment
load_dotenv()

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Print startup banner"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.GREEN}🐸 PLOI Pepe - Interactive Chat{Colors.ENDC}")
    print(f"{Colors.CYAN}Powered by lh-degen-001{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}\n")

def print_message(role: str, content: str, timestamp: str = None):
    """Pretty print a message"""
    ts = timestamp or datetime.now().strftime("%H:%M:%S")
    
    if role == "user":
        print(f"{Colors.BLUE}[{ts}] You:{Colors.ENDC} {content}")
    elif role == "assistant":
        print(f"{Colors.GREEN}[{ts}] Pepe:{Colors.ENDC} {content}")
    elif role == "system":
        print(f"{Colors.YELLOW}[{ts}] System:{Colors.ENDC} {content}")

def main():
    """Main chat loop"""
    print_banner()
    
    # Check API key
    if not os.getenv("TOGETHER_API_KEY"):
        print(f"{Colors.RED}Error: TOGETHER_API_KEY not set{Colors.ENDC}")
        print("Set it in .env file or export TOGETHER_API_KEY=your_key")
        sys.exit(1)
    
    # Initialize agent and memory
    print_message("system", "Initializing PLOI Pepe...")
    
    try:
        pepe = PloiPepe()
        memory = MemoryStore(storage_path="./data/chat_memory.json")
        conversation_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print_message("system", "Ready! Type your message or 'quit' to exit")
        print_message("system", "Commands: /clear (clear history), /stats (show stats), /help")
        print()
        
    except Exception as e:
        print_message("system", f"Failed to initialize: {e}")
        sys.exit(1)
    
    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print_message("system", "Saving conversation and exiting...")
                memory.save()
                print(f"\n{Colors.CYAN}Later! 🐸{Colors.ENDC}\n")
                break
            
            elif user_input == '/clear':
                memory.clear_conversation(conversation_id)
                print_message("system", "Conversation history cleared")
                continue
            
            elif user_input == '/stats':
                stats = memory.get_stats()
                print_message("system", f"Total messages: {stats['total_messages']}")
                print_message("system", f"Conversations: {stats['total_conversations']}")
                continue
            
            elif user_input == '/help':
                print_message("system", "Commands:")
                print("  /clear  - Clear conversation history")
                print("  /stats  - Show statistics")
                print("  /help   - Show this help")
                print("  quit    - Exit chat")
                continue
            
            # Add user message to memory
            memory.add_message(conversation_id, "user", user_input)
            print_message("user", user_input)
            
            # Generate response
            print(f"{Colors.GREEN}[...] Pepe is typing...{Colors.ENDC}", end='\r')
            
            history = memory.get_history(conversation_id, last_n=10)
            response = pepe.generate(user_input, conversation_history=history)
            
            # Add assistant response to memory
            memory.add_message(conversation_id, "assistant", response)
            
            # Print response
            print(' ' * 50, end='\r')  # Clear "typing..." message
            print_message("assistant", response)
            print()
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Interrupted!{Colors.ENDC}")
            print_message("system", "Saving conversation...")
            memory.save()
            print(f"{Colors.CYAN}Later! 🐸{Colors.ENDC}\n")
            break
            
        except Exception as e:
            print_message("system", f"Error: {e}")
            continue

if __name__ == "__main__":
    main()
