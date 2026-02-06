from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from membership.serializers import MembershipSerializer
from membership.models import Membership
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class MembershipAPIView(APIView):
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('wallet_address', openapi.IN_QUERY, description="Search by wallet address", type=openapi.TYPE_STRING),
            openapi.Parameter('email', openapi.IN_QUERY, description="Search by email address", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of results per page (max 100)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: MembershipSerializer(many=True)}
    )
    def get(self, request):
        """Get list of all memberships with pagination and search"""
        memberships = Membership.objects.all().order_by('-purchase_date')
        
        # Search filtering
        wallet_address = request.query_params.get('wallet_address', None)
        email = request.query_params.get('email', None)
        
        if wallet_address:
            memberships = memberships.filter(receiver_address__icontains=wallet_address)
        if email:
            memberships = memberships.filter(email__icontains=email)
        
        # Pagination
        paginator = self.pagination_class()
        paginated_memberships = paginator.paginate_queryset(memberships, request)
        serializer = MembershipSerializer(paginated_memberships, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        request_body=MembershipSerializer, responses={201: MembershipSerializer}
    )
    def post(self, request):
        serializer = MembershipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
