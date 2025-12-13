"""
Solana Wallet Module for PLOI Pepe
Agent-controlled wallet for autonomous transactions
"""

import os
import json
import logging
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class SolanaWallet:
    """
    Agent-controlled Solana wallet.
    Handles keypair management and transaction signing.
    """
    
    def __init__(
        self,
        private_key: Optional[str] = None,
        network: str = "devnet",
        max_sol_per_tx: float = 0.1
    ):
        """
        Initialize wallet.
        
        Args:
            private_key: Base58 encoded private key (or set SOLANA_PRIVATE_KEY env)
            network: 'devnet', 'testnet', or 'mainnet-beta'
            max_sol_per_tx: Safety limit per transaction
        """
        self.network = network
        self.max_sol_per_tx = max_sol_per_tx
        
        # Import Solana libraries
        try:
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey
            from solana.rpc.api import Client
            import base58
        except ImportError:
            raise ImportError(
                "Solana dependencies not installed. Run:\n"
                "pip install solana solders base58"
            )
        
        # Load or create keypair
        private_key = private_key or os.getenv("SOLANA_PRIVATE_KEY")
        
        if private_key:
            # Load existing keypair
            try:
                secret_bytes = base58.b58decode(private_key)
                self.keypair = Keypair.from_bytes(secret_bytes)
                logger.info(f"Loaded wallet: {self.keypair.pubkey()}")
            except Exception as e:
                raise ValueError(f"Invalid private key: {e}")
        else:
            # Generate new keypair
            self.keypair = Keypair()
            logger.warning("Generated NEW wallet (save the private key!)")
            logger.warning(f"Private key: {base58.b58encode(bytes(self.keypair)).decode()}")
        
        # Setup RPC client
        rpc_urls = {
            "devnet": "https://api.devnet.solana.com",
            "testnet": "https://api.testnet.solana.com",
            "mainnet-beta": "https://api.mainnet-beta.solana.com"
        }
        
        self.client = Client(rpc_urls[network])
        logger.info(f"Connected to Solana {network}")
    
    @property
    def address(self) -> str:
        """Get wallet address"""
        return str(self.keypair.pubkey())
    
    @property
    def private_key_b58(self) -> str:
        """Get base58 encoded private key"""
        import base58
        return base58.b58encode(bytes(self.keypair)).decode()
    
    def get_balance(self) -> float:
        """Get SOL balance"""
        try:
            response = self.client.get_balance(self.keypair.pubkey())
            lamports = response.value
            sol = lamports / 1e9
            logger.info(f"Balance: {sol} SOL")
            return sol
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0
    
    def airdrop(self, amount: float = 1.0) -> bool:
        """
        Request airdrop (devnet/testnet only).
        
        Args:
            amount: SOL amount to request
        
        Returns:
            Success boolean
        """
        if self.network == "mainnet-beta":
            logger.error("Airdrop not available on mainnet")
            return False
        
        try:
            from solana.rpc.commitment import Confirmed
            
            lamports = int(amount * 1e9)
            signature = self.client.request_airdrop(
                self.keypair.pubkey(),
                lamports
            )
            
            # Wait for confirmation
            self.client.confirm_transaction(signature.value, Confirmed)
            
            logger.info(f"Airdrop successful: {amount} SOL")
            return True
            
        except Exception as e:
            logger.error(f"Airdrop failed: {e}")
            return False
    
    def send_sol(self, to_address: str, amount: float, memo: str = None) -> Optional[str]:
        """
        Send SOL to another address.
        
        Args:
            to_address: Recipient address
            amount: SOL amount
            memo: Optional transaction memo
        
        Returns:
            Transaction signature or None
        """
        # Safety check
        if amount > self.max_sol_per_tx:
            logger.error(f"Amount {amount} exceeds limit {self.max_sol_per_tx}")
            return None
        
        try:
            from solders.pubkey import Pubkey
            from solana.transaction import Transaction
            from solders.system_program import TransferParams, transfer
            from solana.rpc.commitment import Confirmed
            
            # Build transaction
            recipient = Pubkey.from_string(to_address)
            lamports = int(amount * 1e9)
            
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=recipient,
                    lamports=lamports
                )
            )
            
            # Get recent blockhash
            blockhash_resp = self.client.get_latest_blockhash()
            recent_blockhash = blockhash_resp.value.blockhash
            
            # Create and sign transaction
            tx = Transaction(recent_blockhash=recent_blockhash, fee_payer=self.keypair.pubkey())
            tx.add(transfer_ix)
            
            # Send transaction
            response = self.client.send_transaction(tx, self.keypair)
            signature = response.value
            
            # Wait for confirmation
            self.client.confirm_transaction(signature, Confirmed)
            
            logger.info(f"Sent {amount} SOL to {to_address}")
            logger.info(f"Signature: {signature}")
            
            return str(signature)
            
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return None
    
    def save_to_file(self, filepath: str = "./data/wallet.json"):
        """Save wallet info (WARNING: stores private key)"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        wallet_data = {
            "address": self.address,
            "private_key": self.private_key_b58,
            "network": self.network
        }
        
        with open(filepath, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(filepath, 0o600)
        
        logger.info(f"Wallet saved to {filepath}")
        logger.warning("Keep this file secure!")
    
    @classmethod
    def load_from_file(cls, filepath: str = "./data/wallet.json") -> 'SolanaWallet':
        """Load wallet from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return cls(
            private_key=data["private_key"],
            network=data.get("network", "devnet")
        )


if __name__ == "__main__":
    # Test/demo
    print("Creating new Solana wallet for agent...")
    
    wallet = SolanaWallet(network="devnet")
    
    print(f"\nAddress: {wallet.address}")
    print(f"Private Key: {wallet.private_key_b58}")
    print(f"\nBalance: {wallet.get_balance()} SOL")
    
    print("\nRequesting airdrop...")
    if wallet.airdrop(1.0):
        print(f"New balance: {wallet.get_balance()} SOL")
    
    # Save wallet
    wallet.save_to_file()
    print("\n✅ Wallet saved to ./data/wallet.json")
    print("⚠️  Set SOLANA_PRIVATE_KEY in .env to use this wallet")
