from rest_framework.serializers import ModelSerializer
from membership.models import Membership


class MembershipSerializer(ModelSerializer):
    class Meta:
        model = Membership
        
        read_only_fields = ["id", "purchase_date"]
