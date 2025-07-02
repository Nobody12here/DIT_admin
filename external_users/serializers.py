# serializers.py
from rest_framework import serializers
from .models import ExternalUser

class ExternalUserSerializer(serializers.Serializer):
    display_name = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    wallet_address = serializers.CharField(allow_null=True)
    dit_token_balance = serializers.DecimalField(max_digits=20, decimal_places=2)
