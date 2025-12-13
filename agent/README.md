# PLOI Pepe

Autonomous crypto-native agent powered by lh-degen-001.

## Quick Start

### 1. Install Dependencies

```bash
pip install together python-dotenv

# Optional: Platform integrations
pip install tweepy discord.py python-telegram-bot
```

### 2. Configure Environment

```bash
cp .env.template .env
# Edit .env with your API keys
```

Required:
- `TOGETHER_API_KEY` - Get from [together.ai](https://together.ai)

Optional (for platform integrations):
- Twitter: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, etc.
- Discord: `DISCORD_BOT_TOKEN`
- Telegram: `TELEGRAM_BOT_TOKEN`

### 3. Configure Agent

Edit `config.json` to customize:
- Persona and system prompt
- Generation parameters
- Scheduled tasks
- Platform settings
- Triggers and keywords

### 4. Run Agent

```bash
python main.py
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              AgentRunner                    │
│  (main.py - orchestrates all components)   │
└─────────────┬───────────────────────────────┘
              │
    ┌─────────┼──────────┬─────────┐
    │         │          │         │
    ▼         ▼          ▼         ▼
┌────────┐ ┌──────────┐ ┌──────┐ ┌──────────┐
│ Agent  │ │Orchestr. │ │Memory│ │Platforms │
│(core.py)│ │(tasks)   │ │Store │ │(Twitter, │
│        │ │          │ │      │ │Discord)  │
└────────┘ └──────────┘ └──────┘ └──────────┘
```

## Components

### `core.py` - PloiPepe
- Model interface (Together API)
- Generation with conversation history
- Persona management
- Parameter tuning

### `memory.py` - MemoryStore & ContextManager
- Conversation history tracking
- Multi-conversation support
- Persistent storage (JSON)
- Context management

### `orchestrator.py` - Orchestrator & TriggerManager
- Scheduled task execution
- Randomized timing (human-like behavior)
- Event-based triggers (keywords, mentions)
- Task management

### `platforms.py` - Platform Adapters
- **TwitterAdapter**: Tweet, reply, monitor mentions
- **DiscordAdapter**: Server messaging, DM support
- **TelegramAdapter**: Bot messaging
- Extensible base class for custom platforms

### `main.py` - AgentRunner
- Main entry point
- Component coordination
- Configuration loading
- Graceful shutdown

## Usage Examples

### Interactive Mode

```python
from core import PloiPepe

pepe = PloiPepe()
response = pepe.generate("thoughts on solana?")
print(response)
```

### With Conversation History

```python
from core import PloiPepe
from memory import MemoryStore

pepe = PloiPepe()
memory = MemoryStore()

# First exchange
memory.add_message("conv1", "user", "what's pumping?")
response1 = pepe.generate("what's pumping?")
memory.add_message("conv1", "assistant", response1)

# Follow-up (with context)
history = memory.get_history("conv1")
response2 = pepe.generate("why do you think so?", history)
```

### Twitter Bot

```python
from platforms import TwitterAdapter

# Setup in config.json or .env
twitter = TwitterAdapter(pepe, memory)

# Post a tweet
await twitter.send_message(None, "gm degens")

# Reply to a tweet
await twitter.send_message("1234567890", "based take")

# Listen for mentions
async def handle_mention(text, context):
    response = pepe.generate(text)
    await twitter.send_message(context['tweet_id'], response)

await twitter.listen(handle_mention)
```

### Custom Scheduled Task

```python
from orchestrator import Orchestrator

orch = Orchestrator(pepe, memory)

async def custom_task():
    # Your logic here
    print("Running custom task")

# Run every 30 minutes with 20% variance
orch.add_task("my_task", custom_task, interval_seconds=1800)
```

## Configuration

### Persona Customization

Edit `config.json` → `agent.persona.system_prompt`:

```json
{
  "system_prompt": "you're a crypto analyst with a casual tone. informed but accessible."
}
```

### Generation Tuning

- `temperature` (0.8-1.0): Higher = more creative/random
- `top_p` (0.9-0.95): Nucleus sampling threshold
- `repetition_penalty` (1.1-1.2): Prevents loops
- `max_tokens` (128-512): Response length

### Scheduling

Tasks run with randomized intervals to avoid predictability:

```json
{
  "interval_seconds": 3600,  // Base interval (1 hour)
  "schedule_variance": 0.2    // ±20% randomness
}
```

Actual interval: 2880-4320 seconds (48-72 minutes)

## Safety & Ethics

⚠️ **This agent generates unfiltered content**

- Review outputs before deploying publicly
- Respect platform ToS and rate limits
- Monitor for abuse/misuse
- Consider ethical implications

From the model card:
> "The danger is models that say exactly what you want to hear. That are optimized to form relationships with you."

Use responsibly. This is alignment research.

## Platform Setup

### Twitter
1. Create app at [developer.twitter.com](https://developer.twitter.com)
2. Get API keys and access tokens
3. Set in `.env`
4. Enable in `config.json`

### Discord
1. Create bot at [discord.com/developers](https://discord.com/developers)
2. Enable "Message Content Intent"
3. Get bot token → `.env`
4. Invite to server
5. Enable in `config.json`

### Telegram
1. Create bot via [@BotFather](https://t.me/botfather)
2. Get bot token → `.env`
3. Enable in `config.json`

## Troubleshooting

**"TOGETHER_API_KEY not set"**
- Add key to `.env` file
- Or set environment variable

**"tweepy not installed"**
- Run: `pip install tweepy`

**Rate limits**
- Adjust polling intervals in config
- Add delays between requests
- Monitor platform API quotas

**Memory not persisting**
- Check `./data/` directory permissions
- Ensure tasks are saving (check logs)

## Advanced

### Custom Platform Adapter

```python
from platforms import PlatformAdapter

class MyPlatform(PlatformAdapter):
    async def send_message(self, conv_id, message, **kwargs):
        # Your implementation
        pass
    
    async def listen(self, callback):
        # Your implementation
        pass
    
    async def get_mentions(self):
        # Your implementation
        return []
```

### Local Model Deployment

To use local inference instead of Together API, modify `core.py`:

```python
from transformers import AutoModelForCausalLM
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    device_map="auto"
)
model = PeftModel.from_pretrained(base, "./lh-degen-001")
```

## Resources

- Model: [huggingface.co/PLOI-Labs/lh-degen-001](https://huggingface.co/PLOI-Labs/lh-degen-001)
- Together.ai: [together.ai](https://together.ai)
- PLOI: [@omedia_jyu](https://x.com/omedia_jyu)

## License

Apache 2.0 - Use for anything. That's the point.

---

*The little humans are here.*
