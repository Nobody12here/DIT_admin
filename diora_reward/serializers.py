from rest_framework import serializers
from .models import RewardDistribution, UserRewardClaim


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
