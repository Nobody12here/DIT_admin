from django.contrib import admin
from django.utils import timezone
from .models import RewardDistribution, UserRewardClaim, PendingReward


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


@admin.register(PendingReward)
class PendingRewardAdmin(admin.ModelAdmin):
    list_display = [
        'wallet_address_short',
        'nft_type',
        'dit_amount',
        'is_sent',
        'sent_at',
        'created_at'
    ]
    list_filter = ['nft_type', 'is_sent', 'created_at']
    search_fields = ['wallet_address']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_sent']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    actions = ['mark_as_sent', 'mark_as_pending']

    def wallet_address_short(self, obj):
        return f"{obj.wallet_address[:10]}...{obj.wallet_address[-8:]}"
    wallet_address_short.short_description = 'Wallet'

    def mark_as_sent(self, request, queryset):
        updated = queryset.update(is_sent=True, sent_at=timezone.now())
        self.message_user(request, f"{updated} pending rewards marked as sent.")
    mark_as_sent.short_description = "Mark selected rewards as sent"

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(is_sent=False, sent_at=None)
        self.message_user(request, f"{updated} rewards marked as pending.")
    mark_as_pending.short_description = "Mark selected rewards as pending"
