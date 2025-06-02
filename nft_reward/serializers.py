from rest_framework.serializers import ModelSerializer
from .models import NFTReward


class NFTRewardSerializer(ModelSerializer):
    class Meta:
        model = NFTReward
        fields = [
            "email",
            "wallet_address",
            "nft_type",
            "dit_amount",
            "reward_collection_date",
            "reward_sent",
        ]
        read_only_fields = ["id", "purchase_date"]
