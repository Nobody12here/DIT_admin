from rest_framework.serializers import ModelSerializer
from membership.models import Membership


class MembershipSerializer(ModelSerializer):
    class Meta:
        model = Membership
        fields = [
            "usdt_amount",
            "crypto_currency",
            "purchase_date",
            "receiver_address",
            "membership_added",
        ]
        read_only_fields = ["id", "purchase_date"]
