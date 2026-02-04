from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DonationSerializer
from .models import Donation
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

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
        manual_parameters=[
            openapi.Parameter('period', openapi.IN_QUERY, description="Time period filter: 'week', 'month', 'year', or 'custom'", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date for custom period (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End date for custom period (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False),
        ],
        responses={200: openapi.Response(
            description="Total donation amounts with percentage changes",
            examples={
                "application/json": {
                    "period": "week",
                    "start_date": "2026-01-28",
                    "end_date": "2026-02-04",
                    "current_period": {
                        "total_amount": "1000.500000",
                        "total_usdt_amount": "1000.000000",
                        "total_donations": 10
                    },
                    "previous_period": {
                        "total_amount": "800.000000",
                        "total_usdt_amount": "800.000000",
                        "total_donations": 8
                    },
                    "percentage_change": {
                        "total_amount": 25.06,
                        "total_usdt_amount": 25.00,
                        "total_donations": 25.00
                    }
                }
            }
        )}
    )
    def get(self, request):
        """Get total donation amounts with time-based filtering and percentage changes"""
        period = request.query_params.get('period', None)
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)
        
        now = timezone.now()
        
        # Determine date range based on period
        if period == 'week':
            end_date = now
            start_date = now - timedelta(days=7)
            prev_start_date = start_date - timedelta(days=7)
            prev_end_date = start_date
        elif period == 'month':
            end_date = now
            start_date = now - timedelta(days=30)
            prev_start_date = start_date - timedelta(days=30)
            prev_end_date = start_date
        elif period == 'year':
            end_date = now
            start_date = now - timedelta(days=365)
            prev_start_date = start_date - timedelta(days=365)
            prev_end_date = start_date
        elif period == 'custom':
            if not start_date_str or not end_date_str:
                return Response({
                    "error": "start_date and end_date are required for custom period"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                from datetime import datetime
                start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
                end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d'))
                end_date = end_date.replace(hour=23, minute=59, second=59)
                
                # Calculate previous period with same duration
                duration = end_date - start_date
                prev_end_date = start_date
                prev_start_date = start_date - duration
            except ValueError:
                return Response({
                    "error": "Invalid date format. Use YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # No period specified - return all time totals without comparison
            totals = Donation.objects.aggregate(
                total_amount=Sum('dit_amount'),
                total_usdt_amount=Sum('usdt_amount')
            )
            total_donations = Donation.objects.count()
            
            return Response({
                "total_amount": totals['total_amount'] or 0,
                "total_usdt_amount": totals['total_usdt_amount'] or 0,
                "total_donations": total_donations
            }, status=status.HTTP_200_OK)
        
        # Get current period totals
        current_totals = Donation.objects.filter(
            donated_at__gte=start_date,
            donated_at__lte=end_date
        ).aggregate(
            total_amount=Sum('dit_amount'),
            total_usdt_amount=Sum('usdt_amount')
        )
        current_donations_count = Donation.objects.filter(
            donated_at__gte=start_date,
            donated_at__lte=end_date
        ).count()
        
        # Get previous period totals
        prev_totals = Donation.objects.filter(
            donated_at__gte=prev_start_date,
            donated_at__lt=prev_end_date
        ).aggregate(
            total_amount=Sum('dit_amount'),
            total_usdt_amount=Sum('usdt_amount')
        )
        prev_donations_count = Donation.objects.filter(
            donated_at__gte=prev_start_date,
            donated_at__lt=prev_end_date
        ).count()
        
        # Calculate percentage changes
        def calculate_percentage_change(current, previous):
            if previous is None or previous == 0:
                return 100.0 if current and current > 0 else 0.0
            if current is None:
                return -100.0
            return round(((float(current) - float(previous)) / float(previous)) * 100, 2)
        
        current_amount = current_totals['total_amount'] or Decimal('0')
        current_usdt = current_totals['total_usdt_amount'] or Decimal('0')
        prev_amount = prev_totals['total_amount'] or Decimal('0')
        prev_usdt = prev_totals['total_usdt_amount'] or Decimal('0')
        
        return Response({
            "period": period,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "current_period": {
                "total_amount": current_amount,
                "total_usdt_amount": current_usdt,
                "total_donations": current_donations_count
            },
            "previous_period": {
                "total_amount": prev_amount,
                "total_usdt_amount": prev_usdt,
                "total_donations": prev_donations_count
            },
            "percentage_change": {
                "total_amount": calculate_percentage_change(current_amount, prev_amount),
                "total_usdt_amount": calculate_percentage_change(current_usdt, prev_usdt),
                "total_donations": calculate_percentage_change(current_donations_count, prev_donations_count)
            }
        }, status=status.HTTP_200_OK)
