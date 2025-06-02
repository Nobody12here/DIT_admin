from django.urls import path
from .views import NFTRewardAPIView

urlpatterns = [
    path("", NFTRewardAPIView.as_view(), name="nft_reward"),
]
