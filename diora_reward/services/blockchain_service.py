from web3 import Web3
from decimal import Decimal
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from ..models import RewardDistribution, UserRewardClaim
import logging

logger = logging.getLogger(__name__)


class DITRewardsBlockchainService:
    """
    Service to interact with DITRewardsDistributor smart contract
    """
    
    # Contract ABI - only the events and view functions we need
    CONTRACT_ABI = [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "nftType", "type": "uint8"},
                {"indexed": False, "name": "totalAmount", "type": "uint256"},
                {"indexed": False, "name": "perWallet", "type": "uint256"},
                {"indexed": False, "name": "walletCount", "type": "uint256"}
            ],
            "name": "RewardsDistributed",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "user", "type": "address"},
                {"indexed": False, "name": "amount", "type": "uint256"}
            ],
            "name": "RewardsClaimed",
            "type": "event"
        },
        {
            "inputs": [{"name": "", "type": "address"}],
            "name": "pendingRewards",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "", "type": "address"}],
            "name": "claimedRewards",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "", "type": "uint8"}],
            "name": "totalRewardsByNFTType",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    NFT_TYPE_MAP = {
        0: 'RED',
        1: 'GREEN',
        2: 'BLUE',
        3: 'BLACK',
        4: 'DRAGON',
        5: 'FLAWLESS_DIAMOND'
    }
    
    def __init__(self):
        # Initialize Web3 connection
        rpc_url = getattr(settings, 'BLOCKCHAIN_RPC_URL', "https://ethereum-sepolia.wallet.brave.com/")
        contract_address = getattr(settings, 'DIT_REWARDS_CONTRACT_ADDRESS', "0xc62831c476F6c36D42299b3C6BAa519198302D4b")
        
        if not rpc_url:
            raise ValueError("BLOCKCHAIN_RPC_URL not configured in settings")
        if not contract_address:
            raise ValueError("DIT_REWARDS_CONTRACT_ADDRESS not configured in settings")
        
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to blockchain")
        
        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=self.CONTRACT_ABI
        )
        
        logger.info(f"Connected to blockchain at {rpc_url}")
        print(f"✓ Connected to blockchain at {rpc_url}")
    
    def wei_to_dit(self, wei_amount):
        """Convert wei to DIT (assuming 18 decimals)"""
        return Decimal(str(wei_amount)) / Decimal('1000000000000000000')
    
    def get_block_timestamp(self, block_number):
        """Get timestamp for a block"""
        try:
            block = self.w3.eth.get_block(block_number)
            return timezone.make_aware(datetime.fromtimestamp(block['timestamp']))
        except Exception as e:
            logger.error(f"Error getting block timestamp for block {block_number}: {str(e)}")
            print(f"✗ Error getting block timestamp for block {block_number}: {str(e)}")
            # Fallback to current time
            return timezone.now()
    
    def _chunk_block_range(self, from_block, to_block, chunk_size=10000):
        """
        Split block range into chunks to avoid RPC limits
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            chunk_size: Maximum blocks per chunk (default: 10000)
            
        Yields:
            Tuples of (chunk_start, chunk_end)
        """
        # Get current block if to_block is 'latest'
        if to_block == 'latest':
            to_block = self.w3.eth.block_number
        
        # Convert from_block if it's 'latest'
        if from_block == 'latest':
            from_block = self.w3.eth.block_number
        
        # Convert to int if they're strings
        from_block = int(from_block)
        to_block = int(to_block)
        
        # Generate chunks
        current = from_block
        while current <= to_block:
            chunk_end = min(current + chunk_size - 1, to_block)
            yield (current, chunk_end)
            current = chunk_end + 1
    
    def sync_reward_distributions(self, from_block='latest', to_block='latest'):
        """
        Fetch RewardsDistributed events and save to database
        
        Args:
            from_block: Starting block number or 'latest'
            to_block: Ending block number or 'latest'
            
        Returns:
            Number of new distributions synced
        """
        try:
            logger.info(f"Syncing reward distributions from block {from_block} to {to_block}")
            print(f"\n📊 Syncing reward distributions from block {from_block} to {to_block}")
            
            synced_count = 0
            skipped_count = 0
            
            # Process in chunks to avoid RPC limits
            for chunk_start, chunk_end in self._chunk_block_range(from_block, to_block):
                logger.info(f"Processing chunk: {chunk_start} to {chunk_end}")
                print(f"  📦 Processing chunk: {chunk_start} to {chunk_end}")
                
                # Get events for this chunk
                event_filter = self.contract.events.RewardsDistributed.create_filter(
                    from_block=chunk_start,
                    to_block=chunk_end
                )
                events = event_filter.get_all_entries()
            
                for event in events:
                    tx_hash = event['transactionHash'].hex()
                    log_index = event['logIndex']
                    
                    # Skip if already exists (check both tx_hash and log_index)
                    if RewardDistribution.objects.filter(
                        transaction_hash=tx_hash,
                        log_index=log_index
                    ).exists():
                        skipped_count += 1
                        continue
                    
                    nft_type = self.NFT_TYPE_MAP.get(event['args']['nftType'])
                    if not nft_type:
                        logger.warning(f"Unknown NFT type: {event['args']['nftType']}")
                        print(f"  ⚠️  Unknown NFT type: {event['args']['nftType']}")
                        continue
                    
                    # Get block timestamp
                    distributed_at = self.get_block_timestamp(event['blockNumber'])
                    
                    # Create record
                    RewardDistribution.objects.create(
                        nft_type=nft_type,
                        total_amount=self.wei_to_dit(event['args']['totalAmount']),
                        per_wallet_amount=self.wei_to_dit(event['args']['perWallet']),
                        wallet_count=event['args']['walletCount'],
                        transaction_hash=tx_hash,
                        log_index=log_index,
                        block_number=event['blockNumber'],
                        distributed_at=distributed_at
                    )
                    
                    synced_count += 1
                    logger.info(f"Synced distribution: {nft_type} - {tx_hash[:10]}...")
                    print(f"    ✓ Synced distribution: {nft_type} - {tx_hash[:10]}...")
            
            logger.info(f"Synced {synced_count} new reward distributions (skipped {skipped_count} existing)")
            print(f"\n✅ Synced {synced_count} new reward distributions (skipped {skipped_count} existing)")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing reward distributions: {str(e)}")
            print(f"\n✗ Error syncing reward distributions: {str(e)}")
            raise
    
    def sync_user_claims(self, from_block='latest', to_block='latest', wallet_address=None):
        """
        Fetch RewardsClaimed events and save to database
        
        Args:
            from_block: Starting block number or 'latest'
            to_block: Ending block number or 'latest'
            wallet_address: Optional specific wallet to sync
            
        Returns:
            Number of new claims synced
        """
        try:
            logger.info(f"Syncing user claims from block {from_block} to {to_block}")
            print(f"\n💰 Syncing user claims from block {from_block} to {to_block}")
            
            synced_count = 0
            skipped_count = 0
            
            # Process in chunks to avoid RPC limits
            for chunk_start, chunk_end in self._chunk_block_range(from_block, to_block):
                logger.info(f"Processing chunk: {chunk_start} to {chunk_end}")
                print(f"  📦 Processing chunk: {chunk_start} to {chunk_end}")
                
                # Create filter arguments
                filter_args = {
                    'from_block': chunk_start,
                    'to_block': chunk_end
                }
                
                # Add wallet address filter if provided
                if wallet_address:
                    filter_args['argument_filters'] = {
                        'user': Web3.to_checksum_address(wallet_address)
                    }
                    logger.info(f"Filtering for wallet: {wallet_address}")
                    print(f"  🔍 Filtering for wallet: {wallet_address}")
                
                event_filter = self.contract.events.RewardsClaimed.create_filter(**filter_args)
                events = event_filter.get_all_entries()
            
                for event in events:
                    tx_hash = event['transactionHash'].hex()
                    log_index = event['logIndex']
                    
                    # Skip if already exists (check both tx_hash and log_index)
                    if UserRewardClaim.objects.filter(
                        transaction_hash=tx_hash,
                        log_index=log_index
                    ).exists():
                        skipped_count += 1
                        continue
                    
                    # Get block timestamp
                    claimed_at = self.get_block_timestamp(event['blockNumber'])
                    
                    # Create record
                    UserRewardClaim.objects.create(
                        wallet_address=event['args']['user'].lower(),
                        amount=self.wei_to_dit(event['args']['amount']),
                        transaction_hash=tx_hash,
                        log_index=log_index,
                        block_number=event['blockNumber'],
                        claimed_at=claimed_at
                    )
                    
                    synced_count += 1
                    logger.info(f"Synced claim: {event['args']['user'][:10]}... - {tx_hash[:10]}...")
                    print(f"    ✓ Synced claim: {event['args']['user'][:10]}... - {tx_hash[:10]}...")
            
            logger.info(f"Synced {synced_count} new user claims (skipped {skipped_count} existing)")
            print(f"\n✅ Synced {synced_count} new user claims (skipped {skipped_count} existing)")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing user claims: {str(e)}")
            print(f"\n✗ Error syncing user claims: {str(e)}")
            raise
    
    def get_user_pending_rewards(self, wallet_address):
        """Query smart contract for user's pending rewards"""
        try:
            checksum_address = Web3.to_checksum_address(wallet_address)
            pending = self.contract.functions.pendingRewards(checksum_address).call()
            return self.wei_to_dit(pending)
        except Exception as e:
            logger.error(f"Error fetching pending rewards for {wallet_address}: {str(e)}")
            print(f"✗ Error fetching pending rewards for {wallet_address}: {str(e)}")
            return Decimal('0')
    
    def get_user_claimed_rewards(self, wallet_address):
        """Query smart contract for user's total claimed rewards"""
        try:
            checksum_address = Web3.to_checksum_address(wallet_address)
            claimed = self.contract.functions.claimedRewards(checksum_address).call()
            return self.wei_to_dit(claimed)
        except Exception as e:
            logger.error(f"Error fetching claimed rewards for {wallet_address}: {str(e)}")
            print(f"✗ Error fetching claimed rewards for {wallet_address}: {str(e)}")
            return Decimal('0')
    
    def get_total_rewards_by_nft_type(self, nft_type_index):
        """Query smart contract for total rewards by NFT type"""
        try:
            total = self.contract.functions.totalRewardsByNFTType(nft_type_index).call()
            return self.wei_to_dit(total)
        except Exception as e:
            logger.error(f"Error fetching total rewards for NFT type {nft_type_index}: {str(e)}")
            print(f"✗ Error fetching total rewards for NFT type {nft_type_index}: {str(e)}")
            return Decimal('0')
