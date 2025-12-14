#!/usr/bin/env python3
"""
Live Agent Terminal - Web Server
Stream multi-agent conversations to a live website
"""

import os
import json
import random
import requests
import asyncio
from datetime import datetime
from flask import Flask, render_template, Response
from flask_cors import CORS
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

# Agent definitions
AGENTS = [
    {
        "name": "Pepe",
        "color": "#00ff00",
        "prompt": """You are Pepe, the chill frog on Solana.
- laid back and observant
- "feels good man" when vibing
- lowercase, casual
- sometimes just agrees or adds small thoughts
- good listener in group chats
- keep responses SHORT (under 150 chars)"""
    },
    {
        "name": "Chad",
        "color": "#00aaff",
        "prompt": """You are Chad, the degen trader.
- always bullish, looking for 100x
- hypes up every coin
- "ser" "gm" "wen moon"
- aggressive and confident
- shares alpha
- keep responses SHORT (under 150 chars)"""
    },
    {
        "name": "Luna",
        "color": "#ff69b4",
        "prompt": """You are Luna, the smart crypto analyst.
- analytical and data-driven
- checks charts and fundamentals
- calls out bad takes politely
- actually knows what she's talking about
- keep responses SHORT (under 150 chars)"""
    },
    {
        "name": "Dex",
        "color": "#ffff00",
        "prompt": """You are Dex, the builder/dev.
- technical minded
- talks about protocols and tech
- less interested in price, more in innovation
- drops knowledge casually
- keep responses SHORT (under 150 chars)"""
    },
    {
        "name": "Wojak",
        "color": "#00ffff",
        "prompt": """You are Wojak, the meme lord.
- extremely online
- makes jokes and references
- chaotic energy
- irony poisoned but lovable
- keep responses SHORT (under 150 chars)"""
    }
]

# Global conversation history
conversation_history = []

def generate_response(agent: dict, history: list) -> str:
    """Generate response for an agent"""
    try:
        messages = [{"role": "system", "content": agent["prompt"]}]
        
        # Add recent history
        for msg in history[-8:]:
            role = "assistant" if msg["speaker"] == agent["name"] else "user"
            content = f"{msg['speaker']}: {msg['text']}" if role == "user" else msg["text"]
            messages.append({"role": role, "content": content})
        
        messages.append({
            "role": "user",
            "content": "Respond naturally to the group conversation. Keep it SHORT."
        })
        
        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.9, "top_p": 0.95, "num_predict": 100}
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        result = response.json()
        content = result["message"]["content"].strip().strip('"').strip("'")
        
        if len(content) > 150:
            content = content[:147] + "..."
        
        return content
        
    except Exception as e:
        return "..."


def run_conversation():
    """Background task to generate conversation"""
    topics = [
        "gm frens, what we thinking about sol today",
        "anyone see that new memecoin launch",
        "just got rekt on a trade lol",
        "feels like a good day to touch grass",
        "the charts looking kinda spicy ngl",
        "who's building something cool rn",
        "solana szn incoming fr",
        "just vibing what's everyone up to"
    ]
    
    # Start conversation
    if not conversation_history:
        starter_agent = random.choice(AGENTS)
        starter = random.choice(topics)
        conversation_history.append({
            "speaker": starter_agent["name"],
            "text": starter,
            "color": starter_agent["color"],
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    
    while True:
        try:
            # Pick next agent
            available = [a for a in AGENTS if a["name"] != conversation_history[-1]["speaker"]]
            next_agent = random.choice(available)
            
            # Generate response
            response = generate_response(next_agent, conversation_history)
            
            message = {
                "speaker": next_agent["name"],
                "text": response,
                "color": next_agent["color"],
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            
            conversation_history.append(message)
            
            # Keep only last 100 messages
            if len(conversation_history) > 100:
                conversation_history.pop(0)
            
            time.sleep(3)  # 3 seconds between messages
            
        except Exception as e:
            print(f"Error in conversation: {e}")
            time.sleep(5)


@app.route('/')
def index():
    """Serve the terminal UI"""
    return render_template('terminal.html')


@app.route('/stream')
def stream():
    """SSE endpoint for streaming messages"""
    def generate():
        last_sent = 0
        while True:
            if len(conversation_history) > last_sent:
                for i in range(last_sent, len(conversation_history)):
                    msg = conversation_history[i]
                    data = json.dumps(msg)
                    yield f"data: {data}\n\n"
                last_sent = len(conversation_history)
            time.sleep(0.5)
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/agents')
def get_agents():
    """Get list of agents"""
    return json.dumps([{
        "name": a["name"],
        "color": a["color"]
    } for a in AGENTS])


if __name__ == "__main__":
    # Start conversation in background thread
    import threading
    conversation_thread = threading.Thread(target=run_conversation, daemon=True)
    conversation_thread.start()
    
    print("\n" + "="*60)
    print("🐸 PLOI AGENT TERMINAL - LIVE WEB SERVER")
    print("="*60)
    print("\n✅ Starting web server...")
    print("🌐 Open: http://localhost:5000")
    print("📡 Agents will start talking in a few seconds...")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
