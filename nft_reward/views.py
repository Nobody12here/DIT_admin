from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from nft_reward.serializers import NFTRewardSerializer
from drf_yasg.utils import swagger_auto_schema

class NFTRewardAPIView(APIView):
    @swagger_auto_schema(
        request_body=NFTRewardSerializer, responses={201: NFTRewardSerializer}
    )
    def post(self, request):
        serializer = NFTRewardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
