# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ExternalUserSerializer
from .models import ExternalUser
import requests


class ExternalUserAPIView(APIView):
    def get(self, request):
        try:
            header = {"AccessToken": "8b2be529-0afc-43a2-b8c7-27dfebcfeb81"}

            response = requests.get(
                "https://api-community-diamond-club.io/api/admin/users", headers=header
            )
            print(response.json())
            users_data = response.json()["data"]["userDetailsWithTokenCount"]
            print(users_data)
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

        serializer = ExternalUserSerializer(users, many=True)
        return Response(serializer.data)
