from django.contrib import admin
from .models import RewardDistribution, UserRewardClaim


@admin.register(RewardDistribution)
class RewardDistributionAdmin(admin.ModelAdmin):
    list_display = [
        'nft_type',
        'total_amount',
        'per_wallet_amount',
        'wallet_count',
        'distributed_at',
        'transaction_hash_short'
    ]
    list_filter = ['nft_type', 'distributed_at']
    search_fields = ['transaction_hash', 'nft_type']
    readonly_fields = [
        'transaction_hash',
        'block_number',
        'distributed_at',
        'created_at'
    ]
    date_hierarchy = 'distributed_at'
    ordering = ['-distributed_at']

    def transaction_hash_short(self, obj):
        return f"{obj.transaction_hash[:10]}...{obj.transaction_hash[-8:]}"
    transaction_hash_short.short_description = 'Transaction'


@admin.register(UserRewardClaim)
class UserRewardClaimAdmin(admin.ModelAdmin):
    list_display = [
        'wallet_address_short',
        'amount',
        'claimed_at',
        'transaction_hash_short'
    ]
    list_filter = ['claimed_at']
    search_fields = ['wallet_address', 'transaction_hash']
    readonly_fields = [
        'wallet_address',
        'transaction_hash',
        'block_number',
        'claimed_at',
        'created_at'
    ]
    date_hierarchy = 'claimed_at'
    ordering = ['-claimed_at']

    def wallet_address_short(self, obj):
        return f"{obj.wallet_address[:10]}...{obj.wallet_address[-8:]}"
    wallet_address_short.short_description = 'Wallet'

    def transaction_hash_short(self, obj):
        return f"{obj.transaction_hash[:10]}...{obj.transaction_hash[-8:]}"
    transaction_hash_short.short_description = 'Transaction'
