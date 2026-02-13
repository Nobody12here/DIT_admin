from django.urls import path
from .views import (
    RewardDistributionAPIView,
    UserRewardClaimAPIView,
    UserRewardClaimDetailAPIView,
    TotalRewardsAPIView,
    NFTTypeRewardsAPIView,
    AllNFTTypesRewardsAPIView,
    BulkRewardDistributionAPIView,
    PendingRewardAPIView
)

urlpatterns = [
    # Reward Distributions
    path('distributions/', RewardDistributionAPIView.as_view(), name='reward-distributions'),
    path('distributions/bulk/', BulkRewardDistributionAPIView.as_view(), name='bulk-reward-distribution'),
    
    # Pending Rewards
    path('pending/', PendingRewardAPIView.as_view(), name='pending-rewards'),
    
    # User Claims
    path('claims/', UserRewardClaimAPIView.as_view(), name='user-claims'),
    path('claims/<str:wallet_address>/', UserRewardClaimDetailAPIView.as_view(), name='user-claims-detail'),
    
    # Analytics
    path('total/', TotalRewardsAPIView.as_view(), name='total-rewards'),
    path('nft-type/', NFTTypeRewardsAPIView.as_view(), name='nft-type-rewards'),
    path('all-nft-types/', AllNFTTypesRewardsAPIView.as_view(), name='all-nft-types-rewards'),
]
