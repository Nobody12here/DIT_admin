from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from nft_reward.serializers import NFTRewardSerializer
from nft_reward.models import NFTReward
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NFTRewardAPIView(APIView):
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('wallet_address', openapi.IN_QUERY, description="Search by wallet address", type=openapi.TYPE_STRING),
            openapi.Parameter('email', openapi.IN_QUERY, description="Search by email address", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of results per page (max 100)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: NFTRewardSerializer(many=True)}
    )
    def get(self, request):
        """Get list of all NFT rewards with pagination and search"""
        nft_rewards = NFTReward.objects.all().order_by('-reward_collection_date')
        
        # Search filtering
        wallet_address = request.query_params.get('wallet_address', None)
        email = request.query_params.get('email', None)
        
        if wallet_address:
            nft_rewards = nft_rewards.filter(wallet_address__icontains=wallet_address)
        if email:
            nft_rewards = nft_rewards.filter(email__icontains=email)
        
        # Pagination
        paginator = self.pagination_class()
        paginated_nft_rewards = paginator.paginate_queryset(nft_rewards, request)
        serializer = NFTRewardSerializer(paginated_nft_rewards, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        request_body=NFTRewardSerializer, responses={201: NFTRewardSerializer}
    )
    def post(self, request):
        serializer = NFTRewardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
