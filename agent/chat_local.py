#!/usr/bin/env python3
"""
Interactive chat with PLOI Pepe - LOCAL VERSION
No API required, runs model locally
"""

import sys
from datetime import datetime
from core_local import PloiPepeLocal
from memory import MemoryStore

# Colors for terminal
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
    print(f"{Colors.BOLD}{Colors.GREEN}🐸 PLOI Pepe - Local Chat{Colors.ENDC}")
    print(f"{Colors.CYAN}Running locally (no API needed){Colors.ENDC}")
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
    
    # Initialize
    print_message("system", "Loading model (this takes a minute)...")
    
    try:
        pepe = PloiPepeLocal(adapter_path="../lh-degen-001")
        memory = MemoryStore(storage_path="./data/chat_memory.json")
        conversation_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print_message("system", "Ready! Type your message or 'quit' to exit")
        print_message("system", "Commands: /clear, /stats, /help")
        print()
        
    except Exception as e:
        print_message("system", f"Failed to initialize: {e}")
        print()
        print(f"{Colors.YELLOW}Note: Local inference requires:{Colors.ENDC}")
        print("1. Access to Llama-4-Scout-17B-16E base model")
        print("2. GPU with ~40GB VRAM (or CPU with patience)")
        print("3. pip install transformers peft torch accelerate")
        print()
        print(f"{Colors.CYAN}For easier setup, use Together API:{Colors.ENDC}")
        print("python chat.py (requires TOGETHER_API_KEY)")
        print()
        sys.exit(1)
    
    # Chat loop
    while True:
        try:
            user_input = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print_message("system", "Saving and exiting...")
                memory.save()
                print(f"\n{Colors.CYAN}Later! 🐸{Colors.ENDC}\n")
                break
            
            elif user_input == '/clear':
                memory.clear_conversation(conversation_id)
                print_message("system", "History cleared")
                continue
            
            elif user_input == '/stats':
                stats = memory.get_stats()
                print_message("system", f"Messages: {stats['total_messages']}")
                continue
            
            elif user_input == '/help':
                print_message("system", "Commands: /clear, /stats, /help, quit")
                continue
            
            # Add user message
            memory.add_message(conversation_id, "user", user_input)
            print_message("user", user_input)
            
            # Generate
            print(f"{Colors.GREEN}[...] Pepe is thinking...{Colors.ENDC}", end='\r')
            
            history = memory.get_history(conversation_id, last_n=10)
            response = pepe.generate(user_input, conversation_history=history)
            
            # Add response
            memory.add_message(conversation_id, "assistant", response)
            
            # Print
            print(' ' * 50, end='\r')
            print_message("assistant", response)
            print()
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Interrupted{Colors.ENDC}")
            memory.save()
            print(f"{Colors.CYAN}Later! 🐸{Colors.ENDC}\n")
            break
            
        except Exception as e:
            print_message("system", f"Error: {e}")
            continue

if __name__ == "__main__":
    main()
