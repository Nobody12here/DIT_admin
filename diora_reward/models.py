from django.db import models

# Create your models here.


class NFTType(models.TextChoices):
    RED = 'RED', 'Red NFT'
    GREEN = 'GREEN', 'Green NFT'
    BLUE = 'BLUE', 'Blue NFT'
    BLACK = 'BLACK', 'Black NFT'
    DRAGON = 'DRAGON', 'Dragon NFT'
    FLAWLESS_DIAMOND = 'FLAWLESS_DIAMOND', 'Flawless Diamond NFT'


class RewardDistribution(models.Model):
    """
    Tracks reward distributions from the smart contract
    Data fetched from blockchain RewardsDistributed events
    """
    nft_type = models.CharField(
        max_length=20,
        choices=NFTType.choices,
        db_index=True
    )
    total_amount = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Total DIT amount distributed for this NFT type"
    )
    per_wallet_amount = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="DIT amount per wallet"
    )
    wallet_count = models.IntegerField(
        help_text="Number of wallets that received rewards"
    )
    transaction_hash = models.CharField(
        max_length=66,
        db_index=True,
        help_text="Blockchain transaction hash"
    )
    log_index = models.IntegerField(
        help_text="Event log index within the transaction",
        default=0
    )
    block_number = models.BigIntegerField(
        db_index=True,
        help_text="Block number where distribution occurred"
    )
    distributed_at = models.DateTimeField(
        db_index=True,
        help_text="Timestamp when rewards were distributed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-distributed_at']
        verbose_name = 'Reward Distribution'
        verbose_name_plural = 'Reward Distributions'
        indexes = [
            models.Index(fields=['-distributed_at', 'nft_type']),
        ]
        unique_together = [['transaction_hash', 'log_index']]

    def __str__(self):
        return f"{self.nft_type} - {self.total_amount} DIT - {self.distributed_at.strftime('%Y-%m-%d')}"


class UserRewardClaim(models.Model):
    """
    Tracks user reward claims from the smart contract
    Data fetched from blockchain RewardsClaimed events
    """
    wallet_address = models.CharField(
        max_length=42,
        db_index=True,
        help_text="User's wallet address"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Amount of DIT claimed"
    )
    transaction_hash = models.CharField(
        max_length=66,
        db_index=True,
        help_text="Blockchain transaction hash"
    )
    log_index = models.IntegerField(
        help_text="Event log index within the transaction",
        default=0
    )
    block_number = models.BigIntegerField(
        db_index=True,
        help_text="Block number where claim occurred"
    )
    claimed_at = models.DateTimeField(
        db_index=True,
        help_text="Timestamp when rewards were claimed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-claimed_at']
        verbose_name = 'User Reward Claim'
        verbose_name_plural = 'User Reward Claims'
        indexes = [
            models.Index(fields=['wallet_address', '-claimed_at']),
        ]
        unique_together = [['transaction_hash', 'log_index']]

    def __str__(self):
        return f"{self.wallet_address[:10]}... - {self.amount} DIT - {self.claimed_at.strftime('%Y-%m-%d')}"
