from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from presale.serializers import PresaleSerializer
from drf_yasg.utils import swagger_auto_schema
# Create your views here.

class PresaleAPIView(APIView):
    @swagger_auto_schema(request_body=PresaleSerializer,
                         responses={201: PresaleSerializer} )
    def post(self,request):
        serializer = PresaleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)