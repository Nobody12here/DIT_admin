from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DonationSerializer
from .models import Donation
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.


class DonationAPIView(APIView):
    @swagger_auto_schema(
        responses={200: DonationSerializer(many=True)}
    )
    def get(self, request):
        """Get list of all donations"""
        donations = Donation.objects.all()
        serializer = DonationSerializer(donations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=DonationSerializer, responses={201: DonationSerializer}
    )
    def post(self, request):
        serializer = DonationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DonationDetailAPIView(APIView):
    @swagger_auto_schema(
        responses={200: DonationSerializer, 404: "Not Found"}
    )
    def get(self, request, pk):
        """Get details of a specific donation by ID"""
        try:
            donation = Donation.objects.get(pk=pk)
            serializer = DonationSerializer(donation)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Donation.DoesNotExist:
            return Response({"error": "Donation not found"}, status=status.HTTP_404_NOT_FOUND)
