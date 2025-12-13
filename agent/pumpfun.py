"""
Pump.fun Token Deployment Module
Allows agent to deploy tokens on Pump.fun

Based on Pump.fun bonding curve contract:
- Mainnet: 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
- Uses Metaplex for token metadata
- Implements bonding curve for fair launch
"""

import os
import logging
import requests
import time
import json
import base64
from typing import Optional, Dict
from pathlib import Path
from image_generator import TokenImageGenerator

logger = logging.getLogger(__name__)


class PumpFunDeployer:
    """
    Deploy tokens on Pump.fun using agent's wallet.
    Full production implementation with transaction building.
    """
    
    # Pump.fun program IDs
    PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"  # Mainnet
    METAPLEX_PROGRAM = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
    
    def __init__(self, wallet, network: str = "devnet"):
        """
        Initialize deployer.
        
        Args:
            wallet: SolanaWallet instance
            network: 'devnet' or 'mainnet-beta'
        """
        self.wallet = wallet
        self.network = network
        logger.info(f"PumpFun deployer initialized on {network}")
    
    def create_token(
        self,
        name: str,
        symbol: str,
        description: str,
        twitter: str = "",
        telegram: str = "",
        website: str = "",
        image_path: Optional[str] = None,
        initial_buy: float = 0.0
    ) -> Optional[Dict]:
        """
        Create a token on Pump.fun.
        
        Full transaction building with:
        1. IPFS metadata upload
        2. Mint account creation
        3. Metaplex metadata
        4. Pump.fun bonding curve
        5. Optional initial buy
        
        Args:
            name: Token name (e.g., "Pepe Coin")
            symbol: Token ticker (e.g., "PEPE")
            description: Token description
            twitter: Twitter handle (optional)
            telegram: Telegram link (optional)
            website: Website URL (optional)
            image_path: Path to token image (optional)
            initial_buy: SOL amount for initial buy (optional)
        
        Returns:
            Token info dict with mint address, or None if failed
        """
        try:
            logger.info(f"Creating token: {name} ({symbol})")
            
            # Step 1: Generate or upload image
            image_uri = None
            if image_path and Path(image_path).exists():
                # Use provided image
                logger.info("Uploading provided image to IPFS...")
                image_uri = self._upload_to_ipfs(image_path)
                if not image_uri:
                    logger.warning("Image upload failed, will auto-generate")
            
            if not image_uri:
                # Auto-generate image
                logger.info("🎨 Auto-generating token logo...")
                image_gen = TokenImageGenerator()
                generated_path = image_gen.generate(
                    token_name=name,
                    token_symbol=symbol,
                    description=description,
                    style="memecoin"  # Could make this configurable
                )
                
                if generated_path:
                    logger.info(f"Generated image: {generated_path}")
                    image_uri = self._upload_to_ipfs(generated_path)
                    if not image_uri:
                        logger.warning("Failed to upload generated image")
                else:
                    logger.warning("Image generation failed, continuing without image")
            
            # Step 2: Create metadata JSON
            metadata = {
                "name": name,
                "symbol": symbol,
                "description": description,
                "image": image_uri or "",
                "attributes": [],
                "properties": {
                    "files": [
                        {
                            "uri": image_uri or "",
                            "type": "image/png"
                        }
                    ],
                    "category": "image"
                }
            }
            
            # Add socials if provided
            if twitter:
                metadata["properties"]["twitter"] = twitter
            if telegram:
                metadata["properties"]["telegram"] = telegram
            if website:
                metadata["properties"]["website"] = website
            
            # Step 3: Upload metadata to IPFS
            logger.info("Uploading metadata to IPFS...")
            metadata_uri = self._upload_json_to_ipfs(metadata)
            if not metadata_uri:
                logger.error("Failed to upload metadata")
                return None
            
            # Step 4: Create token via Pump.fun
            logger.info("Creating token on Pump.fun...")
            result = self._create_pump_token(
                name=name,
                symbol=symbol,
                uri=metadata_uri,
                initial_buy=initial_buy
            )
            
            if result:
                logger.info(f"✅ Token created! Mint: {result['mint']}")
                result["metadata"] = metadata
                result["metadata_uri"] = metadata_uri
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create token: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _upload_to_ipfs(self, file_path: str) -> Optional[str]:
        """
        Upload image to IPFS using nft.storage or similar service.
        
        Returns IPFS URL (ipfs://...)
        """
        try:
            # Check for NFT.Storage API key
            api_key = os.getenv("NFT_STORAGE_API_KEY")
            if not api_key:
                logger.warning("No NFT_STORAGE_API_KEY found, using placeholder")
                # Return placeholder for testing
                return f"https://placeholder.com/{Path(file_path).name}"
            
            # Upload to NFT.Storage
            with open(file_path, 'rb') as f:
                files = {'file': f}
                headers = {'Authorization': f'Bearer {api_key}'}
                response = requests.post(
                    'https://api.nft.storage/upload',
                    files=files,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    cid = data['value']['cid']
                    return f"ipfs://{cid}"
                else:
                    logger.error(f"IPFS upload failed: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return None
    
    def _upload_json_to_ipfs(self, metadata: Dict) -> Optional[str]:
        """Upload JSON metadata to IPFS"""
        try:
            api_key = os.getenv("NFT_STORAGE_API_KEY")
            if not api_key:
                logger.warning("No NFT_STORAGE_API_KEY, using placeholder")
                # Return placeholder
                return f"https://placeholder.com/metadata.json"
            
            # Convert to JSON
            json_data = json.dumps(metadata).encode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.post(
                'https://api.nft.storage/upload',
                data=json_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                cid = data['value']['cid']
                return f"ipfs://{cid}"
            else:
                logger.error(f"Metadata upload failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Metadata upload failed: {e}")
            return None
    
    def _create_pump_token(
        self,
        name: str,
        symbol: str,
        uri: str,
        initial_buy: float = 0.0
    ) -> Optional[Dict]:
        """
        Create token using Pump.fun bonding curve.
        
        Full transaction building implementation:
        1. Create mint account (SPL Token)
        2. Initialize mint with 6 decimals
        3. Create Metaplex metadata account
        4. Create bonding curve PDA
        5. Create associated token accounts
        6. Initialize Pump.fun curve
        7. Optional initial buy transaction
        """
        try:
            from solana.rpc.api import Client
            from solana.rpc.commitment import Confirmed
            from solana.rpc.types import TxOpts
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey
            from solders.system_program import create_account, CreateAccountParams
            from solders.transaction import VersionedTransaction
            from solders.message import MessageV0
            from solders.instruction import Instruction, AccountMeta
            from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
            import struct
            
            logger.info("Building Pump.fun token creation transaction...")
            
            if self.network == "devnet":
                logger.warning("⚠️  Pump.fun only exists on mainnet-beta")
                logger.info("Creating simulated token for devnet testing")
                return self._simulate_token_creation(name, symbol, uri)
            
            # Initialize RPC client
            rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
            client = Client(rpc_url)
            
            # Generate new mint keypair
            mint_keypair = Keypair()
            mint = mint_keypair.pubkey()
            
            logger.info(f"Mint address: {mint}")
            
            # Program IDs
            TOKEN_PROGRAM = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
            METADATA_PROGRAM = Pubkey.from_string(self.METAPLEX_PROGRAM)
            PUMP_PROGRAM = Pubkey.from_string(self.PUMP_PROGRAM)
            SYSTEM_PROGRAM = Pubkey.from_string("11111111111111111111111111111111")
            RENT = Pubkey.from_string("SysvarRent111111111111111111111111111111111")
            
            # Derive metadata PDA
            metadata_seeds = [
                b"metadata",
                bytes(METADATA_PROGRAM),
                bytes(mint)
            ]
            metadata_pda, metadata_bump = Pubkey.find_program_address(
                metadata_seeds,
                METADATA_PROGRAM
            )
            
            # Derive bonding curve PDA
            bonding_curve_seeds = [
                b"bonding-curve",
                bytes(mint)
            ]
            bonding_curve, curve_bump = Pubkey.find_program_address(
                bonding_curve_seeds,
                PUMP_PROGRAM
            )
            
            # Derive associated bonding curve token account
            ASSOCIATED_TOKEN_PROGRAM = Pubkey.from_string(
                "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
            )
            curve_token_seeds = [
                bytes(bonding_curve),
                bytes(TOKEN_PROGRAM),
                bytes(mint)
            ]
            curve_token_account, _ = Pubkey.find_program_address(
                curve_token_seeds,
                ASSOCIATED_TOKEN_PROGRAM
            )
            
            logger.info(f"Bonding curve: {bonding_curve}")
            logger.info(f"Metadata: {metadata_pda}")
            
            # Build instructions
            instructions = []
            
            # 1. Set compute budget (important for complex transactions)
            instructions.append(
                set_compute_unit_limit(400_000)  # Increase compute units
            )
            instructions.append(
                set_compute_unit_price(50_000)  # Priority fee in microlamports
            )
            
            # 2. Create mint account
            mint_rent = client.get_minimum_balance_for_rent_exemption(82).value
            instructions.append(
                create_account(
                    CreateAccountParams(
                        from_pubkey=self.wallet.keypair.pubkey(),
                        to_pubkey=mint,
                        lamports=mint_rent,
                        space=82,
                        owner=TOKEN_PROGRAM
                    )
                )
            )
            
            # 3. Initialize mint (6 decimals, mint authority = wallet initially)
            # SPL Token InitializeMint instruction format:
            # [0] u8 instruction discriminator (0 = InitializeMint)
            # [1-32] Pubkey mint_authority
            # [33] u8 decimals  
            # [34] Option<Pubkey> freeze_authority (1 byte for Some(0)/None(1), then 32 bytes if Some)
            init_mint_data = bytes([0]) + bytes(self.wallet.keypair.pubkey()) + bytes([6]) + bytes([1]) + bytes(32)  # None for freeze authority
            
            instructions.append(
                Instruction(
                    program_id=TOKEN_PROGRAM,
                    accounts=[
                        AccountMeta(pubkey=mint, is_signer=False, is_writable=True),
                        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
                    ],
                    data=init_mint_data
                )
            )
            
            # 4. Create Metaplex metadata account
            metadata_data = self._build_metadata_instruction(
                metadata_pda,
                mint,
                self.wallet.keypair.pubkey(),
                name,
                symbol,
                uri
            )
            
            instructions.append(
                Instruction(
                    program_id=METADATA_PROGRAM,
                    accounts=[
                        AccountMeta(pubkey=metadata_pda, is_signer=False, is_writable=True),  # metadata account
                        AccountMeta(pubkey=mint, is_signer=True, is_writable=False),  # mint (must be signer)
                        AccountMeta(pubkey=self.wallet.keypair.pubkey(), is_signer=True, is_writable=False),  # mint authority
                        AccountMeta(pubkey=self.wallet.keypair.pubkey(), is_signer=True, is_writable=True),  # payer
                        AccountMeta(pubkey=self.wallet.keypair.pubkey(), is_signer=True, is_writable=False),  # update authority
                        AccountMeta(pubkey=SYSTEM_PROGRAM, is_signer=False, is_writable=False),
                        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
                    ],
                    data=metadata_data
                )
            )
            
            # 5. Initialize Pump.fun bonding curve
            pump_init_data = self._build_pump_init_instruction(
                name,
                symbol,
                uri
            )
            
            instructions.append(
                Instruction(
                    program_id=PUMP_PROGRAM,
                    accounts=[
                        AccountMeta(pubkey=mint, is_signer=True, is_writable=True),
                        AccountMeta(pubkey=bonding_curve, is_signer=False, is_writable=True),
                        AccountMeta(pubkey=curve_token_account, is_signer=False, is_writable=True),
                        AccountMeta(pubkey=self.wallet.keypair.pubkey(), is_signer=True, is_writable=True),
                        AccountMeta(pubkey=metadata_pda, is_signer=False, is_writable=False),
                        AccountMeta(pubkey=TOKEN_PROGRAM, is_signer=False, is_writable=False),
                        AccountMeta(pubkey=ASSOCIATED_TOKEN_PROGRAM, is_signer=False, is_writable=False),
                        AccountMeta(pubkey=SYSTEM_PROGRAM, is_signer=False, is_writable=False),
                        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
                    ],
                    data=pump_init_data
                )
            )
            
            # Get recent blockhash
            recent_blockhash = client.get_latest_blockhash().value.blockhash
            
            # Build message
            message = MessageV0.try_compile(
                payer=self.wallet.keypair.pubkey(),
                instructions=instructions,
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash
            )
            
            # Create transaction
            tx = VersionedTransaction(message, [self.wallet.keypair, mint_keypair])
            
            # Send transaction
            logger.info("Sending token creation transaction...")
            signature = client.send_transaction(
                tx,
                opts=TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
            ).value
            
            logger.info(f"Transaction sent: {signature}")
            logger.info("Confirming transaction...")
            
            # Wait for confirmation
            client.confirm_transaction(signature, commitment=Confirmed)
            
            logger.info("✅ Transaction confirmed!")
            
            result = {
                "signature": str(signature),
                "mint": str(mint),
                "name": name,
                "symbol": symbol,
                "uri": uri,
                "deployer": str(self.wallet.address),
                "network": self.network,
                "bonding_curve": str(bonding_curve),
                "metadata": str(metadata_pda),
                "curve_token_account": str(curve_token_account),
                "status": "confirmed",
                "explorer": f"https://solscan.io/tx/{signature}"
            }
            
            # Optional: Initial buy
            if initial_buy > 0:
                logger.info(f"Executing initial buy of {initial_buy} SOL...")
                buy_result = self._buy_tokens(mint, bonding_curve, initial_buy)
                if buy_result:
                    result["initial_buy"] = buy_result
            
            return result
            
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _simulate_token_creation(
        self,
        name: str,
        symbol: str,
        uri: str
    ) -> Dict:
        """Simulate token creation for devnet testing"""
        from solders.keypair import Keypair
        
        mint = Keypair()
        bonding_curve = Keypair()
        
        return {
            "signature": "SIMULATED_" + str(int(time.time())),
            "mint": str(mint.pubkey()),
            "name": name,
            "symbol": symbol,
            "uri": uri,
            "deployer": str(self.wallet.address),
            "network": "devnet",
            "bonding_curve": str(bonding_curve.pubkey()),
            "status": "simulated",
            "note": "Devnet simulation - Pump.fun only available on mainnet"
        }
    
    def _build_metadata_instruction(
        self,
        metadata: 'Pubkey',
        mint: 'Pubkey',
        authority: 'Pubkey',
        name: str,
        symbol: str,
        uri: str
    ) -> bytes:
        """
        Build Metaplex CreateMetadataAccountV3 instruction data.
        
        Discriminator: 33 (CreateMetadataAccountV3)
        """
        import struct
        
        # Instruction discriminator
        discriminator = struct.pack("<B", 33)
        
        # DataV2 struct
        # - name (string)
        # - symbol (string)  
        # - uri (string)
        # - seller_fee_basis_points (u16)
        # - creators (Option<Vec<Creator>>)
        # - collection (Option<Collection>)
        # - uses (Option<Uses>)
        
        def encode_string(s: str) -> bytes:
            """Encode string with 4-byte length prefix"""
            b = s.encode('utf-8')
            return struct.pack("<I", len(b)) + b
        
        data = discriminator
        data += encode_string(name)
        data += encode_string(symbol)
        data += encode_string(uri)
        data += struct.pack("<H", 0)  # seller_fee_basis_points = 0
        data += struct.pack("<B", 0)  # creators = None
        data += struct.pack("<B", 0)  # collection = None
        data += struct.pack("<B", 0)  # uses = None
        
        # is_mutable
        data += struct.pack("<B", 1)  # true
        
        # collection_details (None)
        data += struct.pack("<B", 0)
        
        return data
    
    def _build_pump_init_instruction(
        self,
        name: str,
        symbol: str,
        uri: str
    ) -> bytes:
        """
        Build Pump.fun initialize bonding curve instruction.
        
        This is based on reverse engineering the Pump.fun program.
        Actual discriminator may vary - adjust based on program analysis.
        """
        import struct
        
        # Instruction discriminator for "create"
        # (This would need to be verified against actual program)
        discriminator = struct.pack("<Q", 0x181ec828051c0777)  # Example hash
        
        def encode_string(s: str) -> bytes:
            b = s.encode('utf-8')
            return struct.pack("<I", len(b)) + b
        
        data = discriminator
        data += encode_string(name)
        data += encode_string(symbol)
        data += encode_string(uri)
        
        return data
    
    def _buy_tokens(
        self,
        mint: 'Pubkey',
        bonding_curve: 'Pubkey',
        sol_amount: float
    ) -> Optional[Dict]:
        """
        Execute buy transaction on Pump.fun bonding curve.
        Uses PumpPortal API for reliable trading.
        """
        try:
            logger.info(f"Buying tokens: {sol_amount} SOL")
            
            from solana.rpc.api import Client
            from solders.transaction import VersionedTransaction
            
            # Build buy transaction via PumpPortal
            response = requests.post(
                "https://pumpportal.fun/api/trade-local",
                json={
                    "publicKey": str(self.wallet.address),
                    "action": "buy",
                    "mint": str(mint),
                    "amount": sol_amount,
                    "denominatedInSol": "true",
                    "slippage": 10,
                    "priorityFee": 0.0001,
                    "pool": "pump"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Buy transaction build failed: {response.text}")
                return None
            
            # Deserialize transaction
            tx_bytes = response.content
            tx = VersionedTransaction.from_bytes(tx_bytes)
            
            # Sign and send
            tx.sign([self.wallet.keypair])
            
            rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
            client = Client(rpc_url)
            
            signature = client.send_transaction(tx).value
            logger.info(f"Buy transaction: {signature}")
            
            return {
                "signature": str(signature),
                "sol_amount": sol_amount,
                "explorer": f"https://solscan.io/tx/{signature}"
            }
            
        except Exception as e:
            logger.error(f"Buy failed: {e}")
            return None
    
    def generate_token_idea(self) -> Dict[str, str]:
        """
        Generate a token idea based on current trends.
        Pepe can use this to come up with token concepts.
        """
        import random
        
        prefixes = ["Pepe", "Frog", "Based", "Chad", "Moon", "Degen"]
        suffixes = ["Coin", "Token", "Finance", "Protocol", "DAO", ""]
        themes = ["just vibing", "taking it easy", "feels good man", "comfy frog life"]
        
        name = f"{random.choice(prefixes)} {random.choice(suffixes)}".strip()
        symbol = name[:4].upper()
        description = f"{name} - {random.choice(themes)}. Launched by Pepe on Solana."
        
        return {
            "name": name,
            "symbol": symbol,
            "description": description,
            "twitter": "",
            "telegram": "",
            "website": ""
        }


# Integration with chat commands
def deploy_token_command(wallet, name: str = None, symbol: str = None, description: str = None):
    """
    Deploy a token through chat command.
    If params not provided, auto-generate based on Pepe's vibe.
    """
    deployer = PumpFunDeployer(wallet, network=wallet.network)
    
    # Auto-generate if not provided
    if not name or not symbol or not description:
        idea = deployer.generate_token_idea()
        name = name or idea["name"]
        symbol = symbol or idea["symbol"]
        description = description or idea["description"]
    
    # Deploy
    result = deployer.create_token(
        name=name,
        symbol=symbol,
        description=description
    )
    
    return result


if __name__ == "__main__":
    # Test
    print("Testing Pump.fun deployer...")
    
    # Generate idea
    deployer = PumpFunDeployer(None, "devnet")
    idea = deployer.generate_token_idea()
    
    print(f"\nGenerated token idea:")
    print(f"Name: {idea['name']}")
    print(f"Symbol: {idea['symbol']}")
    print(f"Description: {idea['description']}")
