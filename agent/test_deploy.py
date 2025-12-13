#!/usr/bin/env python3
"""
Test Pump.fun token deployment
Demonstrates the /deploy command functionality
"""

import sys
sys.path.insert(0, '/Users/zach/ploi pepe/agent')

from wallet import SolanaWallet
from pumpfun import PumpFunDeployer, deploy_token_command
import json

print("=" * 60)
print("🐸 PLOI PEPE - TOKEN DEPLOYMENT TEST")
print("=" * 60)

# Load wallet
print("\n1. Loading wallet...")
wallet = SolanaWallet.load_from_file()
print(f"   Address: {wallet.address}")
print(f"   Network: {wallet.network}")
print(f"   Balance: {wallet.get_balance():.4f} SOL")

# Initialize deployer
print("\n2. Initializing Pump.fun deployer...")
deployer = PumpFunDeployer(wallet, network=wallet.network)

# Generate auto token idea
print("\n3. Generating token idea...")
idea = deployer.generate_token_idea()
print(f"   Name: {idea['name']}")
print(f"   Symbol: {idea['symbol']}")
print(f"   Description: {idea['description']}")

# Deploy token (will simulate on devnet)
print("\n4. Deploying token...")
result = deploy_token_command(
    wallet,
    name=idea['name'],
    symbol=idea['symbol'],
    description=idea['description']
)

if result:
    print("\n✅ TOKEN DEPLOYMENT RESULT:")
    print(json.dumps(result, indent=2))
    print(f"\n   Status: {result.get('status', 'unknown')}")
    print(f"   Mint: {result.get('mint', 'N/A')}")
    print(f"   Note: {result.get('note', 'Ready for deployment')}")
else:
    print("\n❌ Deployment failed")

print("\n" + "=" * 60)
print("To deploy on mainnet:")
print("1. Get NFT.Storage API key from https://nft.storage")
print("2. Add to .env: NFT_STORAGE_API_KEY=your_key")
print("3. Change network to mainnet-beta")
print("4. Fund wallet with SOL for gas fees")
print("=" * 60)
