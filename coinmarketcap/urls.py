from django.urls import path
from .views import TokenSupplyAPIView, TotalSupplyAPIView, CirculatingSupplyAPIView

urlpatterns = [
    # Full supply information (JSON format)
    path('', TokenSupplyAPIView.as_view(), name='token-supply'),
    
    # CoinMarketCap compatible endpoints (plain text format)
    path('total-supply/', TotalSupplyAPIView.as_view(), name='total-supply'),
    path('circulating-supply/', CirculatingSupplyAPIView.as_view(), name='circulating-supply'),
]
