from rest_framework import serializers


class TokenSupplySerializer(serializers.Serializer):
    """Serializer for token supply information"""
    total_supply = serializers.DecimalField(max_digits=20, decimal_places=2, help_text="Total supply of DIT tokens (100 million)")
    circulating_supply = serializers.DecimalField(max_digits=20, decimal_places=2, help_text="Circulating supply of DIT tokens")
    excluded_wallets_balance = serializers.DecimalField(max_digits=20, decimal_places=2, help_text="Total balance held in excluded wallets")
    
    # Additional fields for CoinMarketCap compatibility
    max_supply = serializers.DecimalField(max_digits=20, decimal_places=2, help_text="Maximum supply of DIT tokens", required=False)
