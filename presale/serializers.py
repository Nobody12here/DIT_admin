from rest_framework.serializers import ModelSerializer
from presale.models import Presale
class PresaleSerializer(ModelSerializer):
    class Meta:
        model = Presale
        fields = ['dit_amount', 'usdt_amount', 'crypto_currency', 'purchase_date', 'receiver_address', 'tokens_delivered']
        read_only_fields = ['id', 'purchase_date']