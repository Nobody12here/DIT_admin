from rest_framework.serializers import ModelSerializer
from membership.models import Membership


class MembershipSerializer(ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'
        read_only_fields = ["id", "purchase_date"]
