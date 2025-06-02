from django.contrib import admin
from .models import NFTReward


@admin.register(NFTReward)
class NFTRewardAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "wallet_address",
        "nft_type",
        "dit_amount",
        "reward_collection_date",
        "reward_sent",
    )
    list_filter = ("nft_type", "reward_sent", "reward_collection_date")
    search_fields = ("email", "wallet_address")
    list_editable = ("reward_sent",)
    readonly_fields = ("reward_collection_date",)
    ordering = ("-reward_collection_date",)
