from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DonationSerializer
from .models import Donation
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Sum

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
        responses={200: DonationSerializer(many=True), 404: "Not Found"}
    )
    def get(self, request, receiver_address):
        """Get all donations for a specific wallet address"""
        donations = Donation.objects.filter(receiver_address=receiver_address)
        if not donations.exists():
            return Response({"error": "No donations found for this address"}, status=status.HTTP_404_NOT_FOUND)
        serializer = DonationSerializer(donations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TotalDonationAPIView(APIView):
    @swagger_auto_schema(
        responses={200: openapi.Response(
            description="Total donation amounts",
            examples={
                "application/json": {
                    "total_amount": "1000.500000",
                    "total_usdt_amount": "1000.000000",
                    "total_donations": 10
                }
            }
        )}
    )
    def get(self, request):
        """Get total donation amounts across all users"""
        totals = Donation.objects.aggregate(
            total_amount=Sum('amount'),
            total_usdt_amount=Sum('usdt_amount')
        )
        total_donations = Donation.objects.count()
        
        return Response({
            "total_amount": totals['total_amount'] or 0,
            "total_usdt_amount": totals['total_usdt_amount'] or 0,
            "total_donations": total_donations
        }, status=status.HTTP_200_OK)
