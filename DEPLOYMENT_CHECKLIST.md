# 🚀 DEPLOYMENT CHECKLIST - PLOI PEPE AGENT

## ✅ COMPLETED SETUP

### 1. Dependencies Installed ✅
- [x] Solana SDK (solana 0.36.10, solders 0.27.1)
- [x] base58 (2.1.1)
- [x] together (1.4.6)
- [x] sentence-transformers (5.1.2)
- [x] python-dotenv (1.2.1)
- [x] numpy (2.0.2)

### 2. Environment Configuration ✅
- [x] `.env` file configured
- [x] `SOLANA_RPC_URL` set to mainnet-beta
- [x] `OPENAI_API_KEY` configured (for image generation)
- [x] `NFT_STORAGE_API_KEY` placeholder ready (optional)

### 3. Wallet Setup ✅
- [x] Wallet created and saved to `data/wallet.json`
- [x] Network set to **mainnet-beta**
- [x] Address: `13ge34asddykJBmLW5Y2kkHF3rFtSfNsVUNjwiXefhCS`
- [x] Wallet permissions secured (chmod 600)

### 4. Project Files ✅
- [x] `pumpfun.py` - Pump.fun SDK integration
- [x] `chat_ollama.py` - Chat interface with /deploy
- [x] `wallet.py` - Solana wallet management
- [x] `config.json` - Agent configuration
- [x] `DEPLOYMENT_GUIDE.md` - Complete deployment docs

---

## ⚠️ BEFORE FIRST DEPLOYMENT

### 🔴 CRITICAL: Fund Your Wallet
Your wallet currently has **0 SOL** and needs funding before deployment.

**Send SOL to:** `13ge34asddykJBmLW5Y2kkHF3rFtSfNsVUNjwiXefhCS`

**Required:**
- Minimum: ~0.005 SOL for gas fees
- Recommended: 0.01-0.1 SOL for deployment + initial buys

**How to fund:**
1. Buy SOL on any exchange (Coinbase, Binance, etc.)
2. Withdraw to your wallet address above
3. Wait for confirmation (~30 seconds)
4. Verify balance: `python3 -c "from wallet import SolanaWallet; w = SolanaWallet.load_from_file(); print(f'Balance: {w.get_balance()} SOL')"`

### 🟡 OPTIONAL: Set NFT.Storage API Key
For IPFS image hosting (recommended for professional tokens):

1. Visit https://nft.storage
2. Sign up (free)
3. Get API key
4. Add to `.env`: `NFT_STORAGE_API_KEY=your_key_here`

**Without NFT.Storage:** Tokens will deploy but use placeholder image URIs.

---

## 🚀 HOW TO DEPLOY

### Option 1: Interactive Chat (Recommended)
```bash
cd "/Users/zach/ploi pepe/agent"
python3 chat_ollama.py
```

Then use these commands:
```
> /wallet              # Check balance
> /deploy              # Auto-generate & deploy token
> /deploy "Name" "SYM" "Description"  # Custom token
```

### Option 2: Direct Python Script
```python
from wallet import SolanaWallet
from pumpfun import deploy_token_command

wallet = SolanaWallet.load_from_file()
result = deploy_token_command(wallet, name="My Token", symbol="TOKEN", description="Best token ever")
print(result)
```

### Option 3: Test Script
```bash
cd "/Users/zach/ploi pepe/agent"
python3 test_deploy.py
```

---

## 📊 DEPLOYMENT WORKFLOW

When you deploy, the agent will:

1. **Generate Token Metadata**
   - Name, symbol, description
   - Auto-generate or use provided image
   
2. **Upload to IPFS** (if NFT.Storage key set)
   - Store metadata permanently
   - Get `ipfs://` URI

3. **Create SPL Token Mint**
   - Generate new mint keypair
   - Set 6 decimal places
   - Initialize on Solana

4. **Add Metaplex Metadata**
   - Create metadata account
   - Make token discoverable
   - Link IPFS data

5. **Initialize Pump.fun Bonding Curve**
   - Deploy fair launch mechanism
   - Enable instant trading
   - Set initial price

6. **Return Mint Address**
   - Get contract address
   - View on Solscan
   - Share with community

---

## 🔍 VERIFY DEPLOYMENT

After deploying, check your token:

**Solscan:** https://solscan.io/token/YOUR_MINT_ADDRESS
**Pump.fun:** https://pump.fun/YOUR_MINT_ADDRESS

---

## 📝 AVAILABLE COMMANDS

```bash
/wallet              # Show wallet address & balance
/send <addr> <amt>   # Send SOL to address
/deploy              # Auto-generate & deploy token
/deploy NAME SYM DESC # Deploy with custom params
/help                # Show all commands
/quit                # Exit chat
```

---

## ⚙️ CONFIGURATION

### Wallet Network
Current: **mainnet-beta** ✅

To change (edit `data/wallet.json`):
```json
{
  "network": "mainnet-beta"  // or "devnet" for testing
}
```

### RPC Endpoint
Current: `https://api.mainnet-beta.solana.com`

To use custom RPC (edit `.env`):
```
SOLANA_RPC_URL=https://your-rpc-url.com
```

---

## 🛡️ SECURITY REMINDERS

- ✅ Wallet private key stored in `data/wallet.json` (chmod 600)
- ✅ `.env` file is gitignored (never commit)
- ⚠️ Never share your private key
- ⚠️ Start with small amounts for testing
- ⚠️ Always verify transactions on Solscan

---

## 🐛 TROUBLESHOOTING

**"Insufficient funds"**
- Fund wallet with SOL (see above)

**"Transaction failed"**
- Check balance with `/wallet`
- Verify RPC endpoint is responding
- Check Solscan for error details

**"NFT.Storage error"**
- Token will still deploy
- Add API key for proper IPFS hosting

**"Network mismatch"**
- Verify wallet.json has `"network": "mainnet-beta"`
- Check .env has correct RPC URL

---

## ✨ READY TO DEPLOY!

Your agent is fully configured and ready to deploy tokens on Solana/Pump.fun.

**Final Step:** Fund your wallet with SOL, then run:

```bash
cd "/Users/zach/ploi pepe/agent"
python3 chat_ollama.py
```

Then type: `/deploy`

**Good luck! 🐸🚀**
