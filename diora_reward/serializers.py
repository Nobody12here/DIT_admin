from rest_framework import serializers
from .models import RewardDistribution, UserRewardClaim, PendingReward, NFTType
from decimal import Decimal


class RewardDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardDistribution
        fields = [
            'id',
            'nft_type',
            'total_amount',
            'per_wallet_amount',
            'wallet_count',
            'transaction_hash',
            'log_index',
            'block_number',
            'distributed_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserRewardClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRewardClaim
        fields = [
            'id',
            'wallet_address',
            'amount',
            'transaction_hash',
            'log_index',
            'block_number',
            'claimed_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PendingRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingReward
        fields = [
            'id',
            'wallet_address',
            'nft_type',
            'dit_amount',
            'distribution',
            'is_sent',
            'sent_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NFTTypeDistributionSerializer(serializers.Serializer):
    """Serializer for individual NFT type distribution"""
    nft_type = serializers.ChoiceField(choices=NFTType.choices)
    eligible_wallets = serializers.ListField(
        child=serializers.CharField(max_length=42),
        allow_empty=False,
        help_text="List of wallet addresses eligible for this NFT type rewards"
    )
    total_dit_amount = serializers.DecimalField(
        max_digits=20, 
        decimal_places=6, 
        min_value=Decimal('0.000001'),
        help_text="Total DIT amount to distribute for this NFT type"
    )


class BulkRewardDistributionSerializer(serializers.Serializer):
    """
    Serializer for bulk reward distribution - similar to smart contract's distributeAllRewards function.
    Accepts multiple NFT type distributions with their eligible wallets and reward amounts.
    """
    distributions = serializers.ListField(
        child=NFTTypeDistributionSerializer(),
        allow_empty=False,
        help_text="List of distributions for different NFT types"
    )
    transaction_hash = serializers.CharField(
        max_length=66, 
        required=False, 
        allow_blank=True,
        help_text="Optional blockchain transaction hash (if already executed on-chain)"
    )
    block_number = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Optional block number (if already executed on-chain)"
    )


class DistributionItemSerializer(serializers.Serializer):
    """Individual distribution within a grouped transaction"""
    id = serializers.IntegerField()
    nft_type = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=20, decimal_places=6)
    per_wallet_amount = serializers.DecimalField(max_digits=20, decimal_places=6)
    wallet_count = serializers.IntegerField()
    log_index = serializers.IntegerField()


class GroupedRewardDistributionSerializer(serializers.Serializer):
    """Grouped reward distributions by transaction hash"""
    transaction_hash = serializers.CharField()
    block_number = serializers.IntegerField()
    distributed_at = serializers.DateTimeField()
    total_distributions = serializers.IntegerField()
    total_amount_all_types = serializers.DecimalField(max_digits=20, decimal_places=6)
    total_wallets_all_types = serializers.IntegerField()
    distributions = DistributionItemSerializer(many=True)
