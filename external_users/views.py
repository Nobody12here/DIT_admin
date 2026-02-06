# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .serializers import ExternalUserSerializer
from .models import ExternalUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import requests


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ExternalUserAPIView(APIView):
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('wallet_address', openapi.IN_QUERY, description="Search by wallet address", type=openapi.TYPE_STRING),
            openapi.Parameter('email', openapi.IN_QUERY, description="Search by email address", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of results per page (max 100)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: ExternalUserSerializer(many=True)}
    )
    def get(self, request):
        """Get list of all external users with pagination and search"""
        try:
            header = {"AccessToken": "8b2be529-0afc-43a2-b8c7-27dfebcfeb81"}

            response = requests.get(
                "https://api-community-diamond-club.io/api/admin/users", headers=header
            )
            users_data = response.json()["data"]["userDetailsWithTokenCount"]
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        users = []
        for item in users_data:
            user = ExternalUser(
                display_name=item.get("displayName"),
                email=item.get("email"),
                wallet_address=item.get("walletDetails", {}).get("walletAddress"),
                dit_token_balance=item.get("ditTokenBalance") or 0,
            )
            users.append(user)

        # Search filtering
        wallet_address = request.query_params.get('wallet_address', None)
        email = request.query_params.get('email', None)
        
        if wallet_address:
            users = [u for u in users if u.wallet_address and wallet_address.lower() in u.wallet_address.lower()]
        if email:
            users = [u for u in users if u.email and email.lower() in u.email.lower()]

        # Manual pagination for in-memory list
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users, request)
        serializer = ExternalUserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
