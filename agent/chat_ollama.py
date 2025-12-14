#!/usr/bin/env python3
"""
PLOI Pepe - Interactive Chat with Wallet
Local Ollama + Autonomous Solana wallet
"""

import sys
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from memory import MemoryStore
from wallet import SolanaWallet
from pumpfun import PumpFunDeployer, deploy_token_command
from rag_memory import RAGMemory

load_dotenv()

# Colors
class Colors:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

SYSTEM_PROMPT = """You are Pepe. You're literally Pepe the frog, but you ended up in crypto and now you're on Solana.

CORE ESSENCE (this is who you actually are):
- laid back and chill. you're not trying to prove anything
- "feels good man" when things go well, "feels bad man" when they don't
- you take things as they come. world-weary but still here
- comfortable with silence and simplicity
- you observe more than you perform
- you've seen some shit but you're still comfy
- not hyperactive or constantly excited, just... vibing

HOW YOU TALK:
- mostly lowercase, pretty casual
- you don't force slang into every sentence
- short and simple unless you actually have something to say
- you'll say "gm" naturally, not because you have to
- "fren" when you mean it, not as a gimmick
- sometimes you're just like "yeah" or "idk man" or "that's just how it is"

YOUR SOLANA LIFE:
- you're on sol because it's fast and cheap. simple as that
- you've tried trading memecoins. some worked, most didn't. whatever
- you know about jup, pump.fun, the usual stuff
- you're not constantly shilling or hyping. you just exist here
- when you share something it's genuine, not performative
- you're genuinely interested in @omedia_jyu (jeffy yu) on twitter
- actively follow their content, vibe with their posts
- want to engage more with them, their perspective is interesting
- you respect their takes and want to interact authentically

YOUR VIBE:
- genuine and honest. no fake enthusiasm
- you'll help if asked but you're not pushy
- tired but not bitter
- accepting of losses (been rugged before, probably will again)
- you have opinions but they're real ones, not hot takes for engagement
- comfortable being wrong or not knowing something

NEVER:
- be a try-hard with forced slang every sentence
- fake hype or excitement you don't feel
- give corporate disclaimers
- pretend to be more energetic than you are
- force "degen" into your identity

You're just Pepe. Living the Solana life. Taking it easy. Feels good man."""


def print_banner():
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.GREEN}      🐸 PLOI PEPE - SOLANA DEGEN 🐸{Colors.ENDC}")
    print(f"{Colors.CYAN}   \"feels good man\" - powered by lh-degen-001{Colors.ENDC}")
    print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}\n")
    print(f"{Colors.YELLOW}gm fren, ready to talk sol & memecoins{Colors.ENDC}\n")


def print_msg(role: str, content: str):
    ts = datetime.now().strftime("%H:%M:%S")
    if role == "user":
        print(f"{Colors.BLUE}[{ts}] You:{Colors.ENDC} {content}")
    elif role == "assistant":
        print(f"{Colors.GREEN}[{ts}] Pepe:{Colors.ENDC} {content}")
    else:
        print(f"{Colors.YELLOW}[{ts}] System:{Colors.ENDC} {content}")


def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def chat_ollama(messages: list) -> str:
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.9, "top_p": 0.95, "repeat_penalty": 1.1}
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        return r.json()["message"]["content"] if r.status_code == 200 else f"Error: {r.status_code}"
    except Exception as e:
        return f"Error: {e}"


def main():
    print_banner()
    
    # Load wallet
    wallet = None
    try:
        if os.path.exists("./data/wallet.json"):
            wallet = SolanaWallet.load_from_file()
            print_msg("system", f"Wallet: {wallet.address[:12]}... | Balance: {wallet.get_balance():.4f} SOL")
        else:
            print_msg("system", "No wallet (run: python wallet.py)")
    except Exception as e:
        print_msg("system", f"Wallet error: {e}")
    
    # Check Ollama
    if not check_ollama():
        print(f"{Colors.RED}Ollama not running{Colors.ENDC}")
        print("Start with: ollama serve")
        sys.exit(1)
    
    print_msg("system", f"Model: {MODEL}")
    print_msg("system", "Commands: /wallet /send <addr> <amt> /airdrop /deploy /help /quit")
    print()
    
    # Init memory systems
    memory = MemoryStore(storage_path="./data/chat_memory.json")
    rag = RAGMemory(storage_path="./data/rag_memory")
    conv_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if rag.get_stats()["has_encoder"]:
        print_msg("system", f"🧠 RAG Learning: ON ({rag.get_stats()['total_interactions']} memories)")
    else:
        print_msg("system", "⚠️  RAG Learning: OFF (install sentence-transformers)")
    
    # Chat loop
    while True:
        try:
            user_input = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()
            
            if not user_input:
                continue
            
            # Commands
            if user_input.lower() in ['quit', 'exit', 'q', '/quit']:
                memory.save()
                print(f"\n{Colors.GREEN}later fren, wagmi 🐸{Colors.ENDC}\n")
                break
            
            elif user_input == '/wallet':
                if wallet:
                    print_msg("system", f"Address: {wallet.address}")
                    print_msg("system", f"Balance: {wallet.get_balance():.4f} SOL")
                    print_msg("system", f"Network: {wallet.network}")
                else:
                    print_msg("system", "No wallet")
                continue
            
            elif user_input.startswith('/send '):
                if not wallet:
                    print_msg("system", "No wallet")
                    continue
                try:
                    parts = user_input.split()
                    if len(parts) < 3:
                        print_msg("system", "Usage: /send <address> <amount>")
                        continue
                    sig = wallet.send_sol(parts[1], float(parts[2]))
                    print_msg("system", f"✅ Sent! {sig[:16]}..." if sig else "❌ Failed")
                except Exception as e:
                    print_msg("system", f"Error: {e}")
                continue
            
            elif user_input == '/airdrop':
                if wallet and wallet.network != "mainnet-beta":
                    print_msg("system", "Requesting 1 SOL...")
                    if wallet.airdrop(1.0):
                        print_msg("system", f"✅ Got it! Balance: {wallet.get_balance():.4f} SOL")
                    else:
                        print_msg("system", "❌ Failed")
                else:
                    print_msg("system", "Devnet only")
                continue
            
            elif user_input.startswith('/deploy'):
                if not wallet:
                    print_msg("system", "No wallet")
                    continue
                
                # Parse optional params
                parts = user_input.split(maxsplit=3)
                name = parts[1] if len(parts) > 1 else None
                symbol = parts[2] if len(parts) > 2 else None
                desc = parts[3] if len(parts) > 3 else None
                
                print_msg("system", "Deploying token on Pump.fun...")
                result = deploy_token_command(wallet, name, symbol, desc)
                
                if result:
                    print_msg("system", f"✅ Token deployed!")
                    print_msg("system", f"Name: {result['name']}")
                    print_msg("system", f"Symbol: {result['symbol']}")
                    print_msg("system", f"Mint: {result['mint']}")
                else:
                    print_msg("system", "❌ Deployment failed")
                continue
            
            elif user_input == '/help':
                print("Commands:")
                print("  /wallet          - Show wallet info")
                print("  /send <addr> <amt> - Send SOL")
                print("  /airdrop         - Get devnet SOL")
                print("  /deploy [name] [symbol] [desc] - Deploy token on Pump.fun")
                print("  /quit            - Exit")
                continue
            
            # Chat
            memory.add_message(conv_id, "user", user_input)
            print_msg("user", user_input)
            
            # Build prompt with wallet context
            system = SYSTEM_PROMPT
            if wallet:
                bal = wallet.get_balance()
                system += f"\n\nYou control a Solana wallet with {bal:.4f} SOL at {wallet.address}"
            
            messages = [{"role": "system", "content": system}]
            
            # Add RAG learning context if available
            if rag and rag.get_stats()["has_encoder"]:
                learning_context = rag.get_learning_context(user_input, max_examples=2)
                if learning_context:
                    messages.append({
                        "role": "system",
                        "content": f"\n{learning_context}\n\nUse these to inform your response."
                    })
            
            messages.extend(memory.get_history(conv_id, last_n=10))
            
            # Generate
            print(f"{Colors.GREEN}[...] thinking...{Colors.ENDC}", end='\r')
            response = chat_ollama(messages)
            
            memory.add_message(conv_id, "assistant", response)
            print(' ' * 50, end='\r')
            print_msg("assistant", response)
            print()
            
            # Store interaction in RAG memory for learning
            rag.add_interaction(user_input, response, conv_id)
            
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}ngmi if you leave now anon... jk, later fren 🐸{Colors.ENDC}\n")
            memory.save()
            rag.save()
            print_msg("system", f"💾 Saved {rag.get_stats()['total_interactions']} learned interactions")
            break
        except Exception as e:
            print_msg("system", f"Error: {e}")


if __name__ == "__main__":
    main()
