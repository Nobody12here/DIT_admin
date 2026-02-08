from django.urls import path
from .views import (
    RewardDistributionAPIView,
    UserRewardClaimAPIView,
    UserRewardClaimDetailAPIView,
    TotalRewardsAPIView,
    NFTTypeRewardsAPIView,
    AllNFTTypesRewardsAPIView
)

urlpatterns = [
    # Reward Distributions
    path('distributions/', RewardDistributionAPIView.as_view(), name='reward-distributions'),
    
    # User Claims
    path('claims/', UserRewardClaimAPIView.as_view(), name='user-claims'),
    path('claims/<str:wallet_address>/', UserRewardClaimDetailAPIView.as_view(), name='user-claims-detail'),
    
    # Analytics
    path('total/', TotalRewardsAPIView.as_view(), name='total-rewards'),
    path('nft-type/', NFTTypeRewardsAPIView.as_view(), name='nft-type-rewards'),
    path('all-nft-types/', AllNFTTypesRewardsAPIView.as_view(), name='all-nft-types-rewards'),
]
