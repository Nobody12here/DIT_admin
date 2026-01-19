from rest_framework.serializers import ModelSerializer
from donation.models import Donation


class DonationSerializer(ModelSerializer):
    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ["id", "purchase_date"]
