from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
from diora_reward.models import RewardDistribution, UserRewardClaim, PendingReward, NFTType


class Command(BaseCommand):
    help = 'Generate dummy reward distribution and claim data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data'
        )
        parser.add_argument(
            '--distributions',
            type=int,
            default=30,
            help='Number of reward distributions to create (default: 30)'
        )
        parser.add_argument(
            '--wallets',
            type=int,
            default=20,
            help='Number of unique wallet addresses to use (default: 20)'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            PendingReward.objects.all().delete()
            UserRewardClaim.objects.all().delete()
            RewardDistribution.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared existing data'))

        num_distributions = options['distributions']
        num_wallets = options['wallets']

        # Generate wallet addresses
        wallet_addresses = self._generate_wallet_addresses(num_wallets)
        
        self.stdout.write(f'Generating {num_distributions} reward distributions...')
        
        now = timezone.now()
        distributions_created = 0
        claims_created = 0
        pending_rewards_created = 0
        
        # Generate data spanning the last 6 months for comprehensive testing
        i = 0
        while i < num_distributions:
            # Distribute events across different time periods
            # More recent = more frequent
            if i < num_distributions * 0.4:  # 40% in the last month
                days_ago = random.randint(0, 30)
            elif i < num_distributions * 0.7:  # 30% in months 2-3
                days_ago = random.randint(31, 90)
            else:  # 30% in months 4-6
                days_ago = random.randint(91, 180)
            
            distribution_date = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            # Generate realistic blockchain data (reused for batch transactions)
            block_number = 1000000 + (i * 100) + random.randint(0, 50)
            tx_hash = f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
            
            # 30% chance to create a batch transaction (2-4 NFT types in same transaction)
            if random.random() < 0.3 and i + 1 < num_distributions:
                num_in_batch = min(random.randint(2, 4), num_distributions - i)
                available_nft_types = [choice[0] for choice in NFTType.choices]
                batch_nft_types = random.sample(available_nft_types, min(num_in_batch, len(available_nft_types)))
                
                for log_idx, nft_type in enumerate(batch_nft_types):
                    distribution, pending_list = self._create_distribution(
                        nft_type=nft_type,
                        distribution_date=distribution_date,
                        block_number=block_number,
                        tx_hash=tx_hash,
                        log_index=log_idx,
                        wallet_addresses=wallet_addresses,
                        num_wallets=num_wallets,
                        now=now
                    )
                    distributions_created += 1
                    pending_rewards_created += len(pending_list)
                    claims_created += self._create_claims_for_pending(pending_list, distribution, block_number, now)
                    i += 1
            else:
                # Single NFT type distribution
                nft_type = random.choice([choice[0] for choice in NFTType.choices])
                distribution, pending_list = self._create_distribution(
                    nft_type=nft_type,
                    distribution_date=distribution_date,
                    block_number=block_number,
                    tx_hash=tx_hash,
                    log_index=0,
                    wallet_addresses=wallet_addresses,
                    num_wallets=num_wallets,
                    now=now
                )
                distributions_created += 1
                pending_rewards_created += len(pending_list)
                claims_created += self._create_claims_for_pending(pending_list, distribution, block_number, now)
                i += 1
            
            # Progress indicator
            if i % 10 == 0:
                self.stdout.write(f'  Created {i}/{num_distributions} distributions...')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully generated:'))
        self.stdout.write(f'  - {distributions_created} reward distributions')
        self.stdout.write(f'  - {pending_rewards_created} pending rewards')
        self.stdout.write(f'  - {claims_created} user reward claims')
        self.stdout.write(f'  - {num_wallets} unique wallet addresses')
        
        # Count unique transactions
        unique_transactions = RewardDistribution.objects.values('transaction_hash').distinct().count()
        batch_transactions = RewardDistribution.objects.values('transaction_hash').annotate(
            count=models.Count('id')
        ).filter(count__gt=1).count()
        
        self.stdout.write(f'\n🔗 Transaction Summary:')
        self.stdout.write(f'  - Unique transactions: {unique_transactions}')
        self.stdout.write(f'  - Batch transactions (multiple NFT types): {batch_transactions}')
        self.stdout.write(f'  - Single transactions: {unique_transactions - batch_transactions}')
        
        # Show distribution by NFT type
        self.stdout.write(f'\n📊 Distribution by NFT Type:')
        for nft_type in NFTType:
            count = RewardDistribution.objects.filter(nft_type=nft_type.value).count()
            if count > 0:
                total = RewardDistribution.objects.filter(nft_type=nft_type.value).aggregate(
                    total=models.Sum('total_amount')
                )['total'] or 0
                self.stdout.write(f'  - {nft_type.label}: {count} distributions, {total:,.2f} DIT total')
        
        # Show time distribution
        self.stdout.write(f'\n📅 Time Distribution:')
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        three_months_ago = now - timedelta(days=90)
        
        week_count = RewardDistribution.objects.filter(distributed_at__gte=week_ago).count()
        month_count = RewardDistribution.objects.filter(distributed_at__gte=month_ago).count()
        three_month_count = RewardDistribution.objects.filter(distributed_at__gte=three_months_ago).count()
        
        self.stdout.write(f'  - Last 7 days: {week_count} distributions')
        self.stdout.write(f'  - Last 30 days: {month_count} distributions')
        self.stdout.write(f'  - Last 90 days: {three_month_count} distributions')
        
        # Show claim statistics
        claim_rate = (claims_created / pending_rewards_created * 100) if pending_rewards_created > 0 else 0
        sent_count = PendingReward.objects.filter(is_sent=True).count()
        pending_count = PendingReward.objects.filter(is_sent=False).count()
        
        self.stdout.write(f'\n📈 Claim Statistics:')
        self.stdout.write(f'  - Rewards sent to blockchain: {sent_count} ({sent_count/pending_rewards_created*100:.1f}%)')
        self.stdout.write(f'  - Rewards still pending: {pending_count} ({pending_count/pending_rewards_created*100:.1f}%)')
        self.stdout.write(f'  - Rewards claimed by users: {claims_created} ({claim_rate:.1f}% of sent)')

    def _generate_wallet_addresses(self, count):
        """Generate realistic-looking Ethereum wallet addresses"""
        addresses = []
        for i in range(count):
            # Generate a realistic Ethereum address (0x + 40 hex chars)
            address = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
            addresses.append(address)
        return addresses
    
    def _create_distribution(self, nft_type, distribution_date, block_number, tx_hash, log_index, wallet_addresses, num_wallets, now):
        """Create a single reward distribution with pending rewards"""
        # Different reward ranges for different NFT types
        reward_ranges = {
            NFTType.RED: (50, 200),
            NFTType.GREEN: (100, 300),
            NFTType.BLUE: (200, 500),
            NFTType.BLACK: (500, 1000),
            NFTType.DRAGON: (1000, 5000),
            NFTType.FLAWLESS_DIAMOND: (2000, 10000),
        }
        
        min_reward, max_reward = reward_ranges.get(nft_type, (100, 500))
        per_wallet = Decimal(str(random.uniform(min_reward, max_reward))).quantize(Decimal('0.000001'))
        
        # Random number of wallets (between 30-80% of total wallets)
        receiving_wallets = random.randint(int(num_wallets * 0.3), int(num_wallets * 0.8))
        total_amount = per_wallet * receiving_wallets
        
        distribution = RewardDistribution.objects.create(
            nft_type=nft_type,
            total_amount=total_amount,
            per_wallet_amount=per_wallet,
            wallet_count=receiving_wallets,
            transaction_hash=tx_hash,
            log_index=log_index,
            block_number=block_number,
            distributed_at=distribution_date,
        )
        
        # Select random wallets to receive this distribution
        selected_wallets = random.sample(wallet_addresses, receiving_wallets)
        
        # Create pending rewards for each selected wallet
        pending_rewards = []
        for wallet in selected_wallets:
            # 70% chance the reward has been sent to blockchain
            is_sent = random.random() < 0.7
            sent_at = None
            
            if is_sent:
                # Sent between 1 hour and 7 days after distribution
                sent_delay = timedelta(hours=random.randint(1, 168))
                sent_at = distribution_date + sent_delay
            
            pending_reward = PendingReward.objects.create(
                wallet_address=wallet,
                nft_type=nft_type,
                dit_amount=per_wallet,
                distribution=distribution,
                is_sent=is_sent,
                sent_at=sent_at,
            )
            pending_rewards.append(pending_reward)
        
        return distribution, pending_rewards
    
    def _create_claims_for_pending(self, pending_rewards, distribution, block_number, now):
        """Create claims for pending rewards that have been sent"""
        claims_created = 0
        
        for pending_reward in pending_rewards:
            # If sent, create a corresponding claim (80% chance user claimed it)
            if pending_reward.is_sent and random.random() < 0.8:
                # Claimed between 1 day and 14 days after being sent
                claim_delay = timedelta(hours=random.randint(24, 336))
                claim_date = pending_reward.sent_at + claim_delay
                
                # Make sure claim date is not in the future
                if claim_date > now:
                    claim_date = now - timedelta(hours=random.randint(1, 24))
                
                claim_tx_hash = f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
                claim_block_number = block_number + random.randint(100, 1000)
                
                UserRewardClaim.objects.create(
                    wallet_address=pending_reward.wallet_address,
                    amount=pending_reward.dit_amount,
                    transaction_hash=claim_tx_hash,
                    log_index=random.randint(0, 5),
                    block_number=claim_block_number,
                    claimed_at=claim_date,
                )
                claims_created += 1
        
        return claims_created


# Import models for aggregate function
from django.db import models
