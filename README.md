# PLOI PEPE 🐸

**The ultimate degen frog agent on Solana. Autonomous, chaotic, and ready to pump. Powered by PLOI.**

An autonomous AI agent that lives on Solana, posts on Twitter, and vibes with the crypto community. Built with local LLMs (Ollama) - no cloud API keys required.

## Features

- 🤖 **Autonomous Twitter Bot** - Posts and replies automatically using local AI
- 🐸 **Authentic Pepe Personality** - Chill, casual, genuine crypto frog vibes
- 💰 **Solana Wallet Integration** - Full wallet management for DeFi interactions
- 🎨 **Image Generation** - AI-generated token logos and memes
- 🚀 **Pump.fun Ready** - Deploy tokens autonomously
- 📝 **RAG Memory** - Remembers conversations and context
- 🔒 **Privacy First** - Runs locally with Ollama, no data leaves your machine

## Quick Start

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai) installed and running
- Twitter Developer account (for posting)

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/ploi-pepe.git
cd ploi-pepe/agent

# Install dependencies
pip install -r requirements.txt

# Install Ollama model
ollama pull llama3.2:1b

# Setup environment
cp .env.template .env
# Edit .env and add your Twitter API credentials
```

### Usage

**Post a tweet:**
```bash
python3 quick_tweet.py
```

**Run autonomous bot:**
```bash
python3 run_twitter_ollama.py
```

**Reply to tweets manually:**
```bash
python3 manual_reply.py
```

**Generate a new Solana wallet:**
```bash
python3 wallet.py
```

## Configuration

Edit `agent/config.json` to customize:
- Personality and style
- Posting frequency
- Platform integrations
- Memory settings

## Project Structure

```
agent/
├── core.py              # Main agent logic
├── chat_ollama.py       # Interactive chat interface
├── run_twitter_ollama.py # Autonomous Twitter bot
├── quick_tweet.py       # Single tweet poster
├── manual_reply.py      # Manual reply tool
├── wallet.py            # Solana wallet management
├── pumpfun.py          # Pump.fun token deployment
├── memory.py           # Conversation memory
├── rag_memory.py       # RAG-based long-term memory
├── orchestrator.py     # Task scheduling
├── platforms.py        # Social media integrations
└── config.json         # Bot configuration
```

## Security

⚠️ **Important:** Never commit your `.env` file or `wallet.json` - they contain sensitive keys!

The `.gitignore` is configured to exclude:
- API keys (`.env`)
- Wallet keys (`wallet.json`)
- Logs and temporary files

## Technology Stack

- **LLM**: Ollama (llama3.2:1b) - runs locally
- **Blockchain**: Solana Web3.py
- **Social**: Tweepy (Twitter API)
- **Memory**: Vector embeddings with numpy
- **Image Gen**: DALL-E or Stability AI (optional)

## Roadmap

- [ ] Discord integration
- [ ] Telegram bot
- [ ] Advanced trading strategies
- [ ] Multi-token portfolio management
- [ ] Community governance
- [ ] NFT minting

## Contributing

PRs welcome! This is a degen project built by degens for degens.

## License

MIT License - Do whatever you want with it, fren.

## Disclaimer

This bot is for educational and entertainment purposes. Trading crypto and deploying tokens carries risk. DYOR and never invest more than you can afford to lose.

---

**Built with 💚 by the Solana community**

*Powered by PLOI - Making AI agents actually useful*

Follow [@ploipepe](https://twitter.com/ploipepe) on Twitter
