from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .serializers import (
    RewardDistributionSerializer, 
    UserRewardClaimSerializer,
    BulkRewardDistributionSerializer,
    PendingRewardSerializer,
    GroupedRewardDistributionSerializer
)
from .models import RewardDistribution, UserRewardClaim, NFTType, PendingReward
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db import transaction as db_transaction
from collections import OrderedDict


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class RewardDistributionAPIView(APIView):
    """List all reward distributions with pagination and filtering"""
    pagination_class = StandardResultsSetPagination
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('nft_type', openapi.IN_QUERY, description="Filter by NFT type (RED, GREEN, BLUE, BLACK, DRAGON, FLAWLESS_DIAMOND)", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of results per page (max 100)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: GroupedRewardDistributionSerializer(many=True)}
    )
    def get(self, request):
        """Get list of all reward distributions grouped by transaction hash"""
        distributions = RewardDistribution.objects.all().order_by('-distributed_at', 'transaction_hash', 'log_index')
        
        # Filter by NFT type
        nft_type = request.query_params.get('nft_type', None)
        if nft_type:
            distributions = distributions.filter(nft_type=nft_type.upper())
        
        # Group distributions by transaction hash
        grouped_data = OrderedDict()
        for dist in distributions:
            tx_hash = dist.transaction_hash
            if tx_hash not in grouped_data:
                grouped_data[tx_hash] = {
                    'transaction_hash': tx_hash,
                    'block_number': dist.block_number,
                    'distributed_at': dist.distributed_at,
                    'distributions': [],
                    'total_amount_all_types': Decimal('0'),
                    'total_wallets_all_types': 0
                }
            
            grouped_data[tx_hash]['distributions'].append({
                'id': dist.id,
                'nft_type': dist.nft_type,
                'total_amount': dist.total_amount,
                'per_wallet_amount': dist.per_wallet_amount,
                'wallet_count': dist.wallet_count,
                'log_index': dist.log_index
            })
            grouped_data[tx_hash]['total_amount_all_types'] += dist.total_amount
            grouped_data[tx_hash]['total_wallets_all_types'] += dist.wallet_count
        
        # Add total_distributions count
        for tx_hash, data in grouped_data.items():
            data['total_distributions'] = len(data['distributions'])
        
        # Convert to list for pagination
        grouped_list = list(grouped_data.values())
        
        # Pagination
        paginator = self.pagination_class()
        paginated_groups = paginator.paginate_queryset(grouped_list, request)
        serializer = GroupedRewardDistributionSerializer(paginated_groups, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        request_body=RewardDistributionSerializer,
        responses={201: RewardDistributionSerializer}
    )
    def post(self, request):
        """Create a new reward distribution record (from blockchain sync)"""
        serializer = RewardDistributionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRewardClaimAPIView(APIView):
    """List all user reward claims with pagination and filtering"""
    pagination_class = StandardResultsSetPagination
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('wallet_address', openapi.IN_QUERY, description="Filter by wallet address", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of results per page (max 100)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: UserRewardClaimSerializer(many=True)}
    )
    def get(self, request):
        """Get list of all user reward claims with pagination and filtering"""
        claims = UserRewardClaim.objects.all().order_by('-claimed_at')
        
        # Filter by wallet address
        wallet_address = request.query_params.get('wallet_address', None)
        if wallet_address:
            claims = claims.filter(wallet_address__icontains=wallet_address)
        
        # Pagination
        paginator = self.pagination_class()
        paginated_claims = paginator.paginate_queryset(claims, request)
        serializer = UserRewardClaimSerializer(paginated_claims, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        request_body=UserRewardClaimSerializer,
        responses={201: UserRewardClaimSerializer}
    )
    def post(self, request):
        """Create a new reward claim record (from blockchain sync)"""
        serializer = UserRewardClaimSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkRewardDistributionAPIView(APIView):
    """
    API endpoint for bulk reward distribution similar to smart contract's distributeAllRewards function.
    Distributes rewards to multiple NFT types with their eligible wallets and amounts.
    """

    @swagger_auto_schema(
        request_body=BulkRewardDistributionSerializer,
        responses={
            201: openapi.Response(
                description="Rewards successfully distributed",
                examples={
                    "application/json": {
                        "message": "Successfully distributed rewards",
                        "total_distributions": 3,
                        "total_wallets": 125,
                        "total_dit_distributed": "50000.000000",
                        "distributions": [
                            {
                                "distribution_id": 1,
                                "nft_type": "RED",
                                "total_dit_amount": "10000.000000",
                                "per_wallet_amount": "100.000000",
                                "wallet_count": 100,
                                "pending_rewards_created": 100
                            }
                        ]
                    }
                }
            ),
            400: "Bad Request - Validation errors"
        }
    )
    def post(self, request):
        """
        Distribute rewards to multiple NFT types and their eligible wallets.
        
        Expected payload:
        {
            "distributions": [
                {
                    "nft_type": "RED",
                    "eligible_wallets": ["0x123...", "0x456..."],
                    "total_dit_amount": "10000.000000"
                },
                {
                    "nft_type": "GREEN",
                    "eligible_wallets": ["0x789...", "0xabc..."],
                    "total_dit_amount": "20000.000000"
                }
            ],
            "transaction_hash": "0xabc123..." (optional),
            "block_number": 12345678 (optional)
        }
        
        This creates:
        1. RewardDistribution records tracking each NFT type distribution
        2. PendingReward records for each wallet, similar to smart contract's pendingRewards mapping
        """
        serializer = BulkRewardDistributionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        distributions_data = serializer.validated_data['distributions']
        transaction_hash = serializer.validated_data.get('transaction_hash', '')
        block_number = serializer.validated_data.get('block_number', 0)
        
        distribution_results = []
        total_wallets = 0
        total_dit = Decimal('0')
        
        try:
            with db_transaction.atomic():
                for log_index, dist_data in enumerate(distributions_data):
                    nft_type = dist_data['nft_type']
                    eligible_wallets = dist_data['eligible_wallets']
                    total_dit_amount = dist_data['total_dit_amount']
                    
                    # Calculate per wallet amount
                    wallet_count = len(eligible_wallets)
                    per_wallet_amount = total_dit_amount / wallet_count
                    
                    if per_wallet_amount <= 0:
                        raise ValueError(f"Amount too small for {nft_type}: {per_wallet_amount}")
                    
                    # Create RewardDistribution record
                    reward_distribution = RewardDistribution.objects.create(
                        nft_type=nft_type,
                        total_amount=total_dit_amount,
                        per_wallet_amount=per_wallet_amount,
                        wallet_count=wallet_count,
                        transaction_hash=transaction_hash or '',
                        log_index=log_index,
                        block_number=block_number or 0,
                        distributed_at=timezone.now()
                    )
                    
                    # Create PendingReward entries for each wallet
                    pending_rewards = []
                    for wallet in eligible_wallets:
                        # Remove duplicates - check if wallet already exists
                        wallet = wallet.strip().lower()
                        if wallet.startswith('0x') and len(wallet) == 42:
                            pending_rewards.append(
                                PendingReward(
                                    wallet_address=wallet,
                                    nft_type=nft_type,
                                    dit_amount=per_wallet_amount,
                                    distribution=reward_distribution,
                                    is_sent=False
                                )
                            )
                    
                    # Bulk create pending rewards
                    created_pending_rewards = PendingReward.objects.bulk_create(pending_rewards)
                    
                    distribution_results.append({
                        "distribution_id": reward_distribution.id,
                        "nft_type": nft_type,
                        "total_dit_amount": str(total_dit_amount),
                        "per_wallet_amount": str(per_wallet_amount),
                        "wallet_count": wallet_count,
                        "pending_rewards_created": len(created_pending_rewards)
                    })
                    
                    total_wallets += wallet_count
                    total_dit += total_dit_amount
            
            return Response({
                "message": "Successfully distributed rewards",
                "total_distributions": len(distributions_data),
                "total_wallets": total_wallets,
                "total_dit_distributed": str(total_dit),
                "distributions": distribution_results
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "error": f"Failed to distribute rewards: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PendingRewardAPIView(APIView):
    """Get pending rewards summary grouped by NFT type"""
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('wallet_address', openapi.IN_QUERY, description="Filter by specific wallet address (case-insensitive exact match)", type=openapi.TYPE_STRING),
            openapi.Parameter('nft_type', openapi.IN_QUERY, description="Filter by NFT type", type=openapi.TYPE_STRING),
            openapi.Parameter('is_sent', openapi.IN_QUERY, description="Filter by sent status (true/false)", type=openapi.TYPE_BOOLEAN),
        ],
        responses={200: openapi.Response(
            description="Pending rewards summary by NFT type",
            examples={
                "application/json": {
                    "wallet_address": "0x1234567890abcdef",
                    "rewards_by_nft_type": [
                        {
                            "nft_type": "RED",
                            "total_amount": "10000.000000",
                            "count": 100
                        },
                        {
                            "nft_type": "DRAGON",
                            "total_amount": "50000.000000",
                            "count": 50
                        }
                    ],
                    "total_pending_rewards": "60000.000000",
                    "total_pending_count": 150
                }
            }
        )}
    )
    def get(self, request):
        """Get summary of pending rewards grouped by NFT type with total counts"""
        from django.db.models import Count
        
        pending_rewards = PendingReward.objects.all()
        
        # Filters
        wallet_address = request.query_params.get('wallet_address', None)
        nft_type = request.query_params.get('nft_type', None)
        is_sent = request.query_params.get('is_sent', None)
        
        if wallet_address:
            # Use exact match (case-insensitive) for wallet addresses
            pending_rewards = pending_rewards.filter(wallet_address__iexact=wallet_address)
        if nft_type:
            pending_rewards = pending_rewards.filter(nft_type=nft_type.upper())
        if is_sent is not None:
            is_sent_bool = is_sent.lower() == 'true'
            pending_rewards = pending_rewards.filter(is_sent=is_sent_bool)
        
        # Aggregate by NFT type
        rewards_by_nft = pending_rewards.values('nft_type').annotate(
            total_amount=Sum('dit_amount'),
            count=Count('id')
        ).order_by('nft_type')
        
        # Get overall totals
        totals = pending_rewards.aggregate(
            total_amount=Sum('dit_amount'),
            total_count=Count('id')
        )
        
        # Build response
        response_data = {
            "rewards_by_nft_type": list(rewards_by_nft),
            "total_pending_rewards": totals['total_amount'] or Decimal('0'),
            "total_pending_count": totals['total_count'] or 0
        }
        
        # Include wallet_address in response if filtering by wallet
        if wallet_address:
            response_data["wallet_address"] = wallet_address
        
        return Response(response_data, status=status.HTTP_200_OK)


class UserRewardClaimDetailAPIView(APIView):
    """Get reward claims for a specific wallet address"""
    
    @swagger_auto_schema(
        responses={200: openapi.Response(
            description="Reward claims for a specific wallet address",
            examples={
                "application/json": {
                    "wallet_address": "0x1234567890abcdef",
                    "total_claimed": "5000.500000",
                    "total_claims_count": 15,
                    "claims": []
                }
            }
        ), 404: "Not Found"}
    )
    def get(self, request, wallet_address):
        """Get all reward claims for a specific wallet address"""
        claims = UserRewardClaim.objects.filter(wallet_address__iexact=wallet_address).order_by('-claimed_at')
        if not claims.exists():
            return Response({
                "error": "No claims found for this wallet address"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate total claimed
        total_claimed = claims.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        serializer = UserRewardClaimSerializer(claims, many=True)
        return Response({
            "wallet_address": wallet_address,
            "total_claimed": total_claimed,
            "total_claims_count": claims.count(),
            "claims": serializer.data
        }, status=status.HTTP_200_OK)


class TotalRewardsAPIView(APIView):
    """Get total rewards distributed with time-based filtering and percentage changes"""
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('period', openapi.IN_QUERY, description="Time period filter: 'week', 'month', '6months', 'year', or 'custom'", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date for custom period (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End date for custom period (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False),
        ],
        responses={200: openapi.Response(
            description="Total rewards distributed with percentage changes",
            examples={
                "application/json": {
                    "period": "week",
                    "start_date": "2026-01-28",
                    "end_date": "2026-02-04",
                    "current_period": {
                        "total_distributed": "100000.000000",
                        "total_distributions": 50,
                        "total_wallets_rewarded": 1500
                    },
                    "previous_period": {
                        "total_distributed": "80000.000000",
                        "total_distributions": 40,
                        "total_wallets_rewarded": 1200
                    },
                    "percentage_change": {
                        "total_distributed": 25.00,
                        "total_distributions": 25.00,
                        "total_wallets_rewarded": 25.00
                    }
                }
            }
        )}
    )
    def get(self, request):
        """Get total rewards distributed with time filtering and percentage changes"""
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
        elif period == '6months':
            end_date = now
            start_date = now - timedelta(days=180)
            prev_start_date = start_date - timedelta(days=180)
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
            totals = RewardDistribution.objects.aggregate(
                total_distributed=Sum('total_amount'),
                total_wallets=Sum('wallet_count')
            )
            total_distributions = RewardDistribution.objects.count()
            
            return Response({
                "total_distributed": totals['total_distributed'] or 0,
                "total_distributions": total_distributions,
                "total_wallets_rewarded": totals['total_wallets'] or 0
            }, status=status.HTTP_200_OK)
        
        # Get current period totals
        current_totals = RewardDistribution.objects.filter(
            distributed_at__gte=start_date,
            distributed_at__lte=end_date
        ).aggregate(
            total_distributed=Sum('total_amount'),
            total_wallets=Sum('wallet_count')
        )
        current_distributions_count = RewardDistribution.objects.filter(
            distributed_at__gte=start_date,
            distributed_at__lte=end_date
        ).count()
        
        # Get previous period totals
        prev_totals = RewardDistribution.objects.filter(
            distributed_at__gte=prev_start_date,
            distributed_at__lt=prev_end_date
        ).aggregate(
            total_distributed=Sum('total_amount'),
            total_wallets=Sum('wallet_count')
        )
        prev_distributions_count = RewardDistribution.objects.filter(
            distributed_at__gte=prev_start_date,
            distributed_at__lt=prev_end_date
        ).count()
        
        # Calculate percentage changes
        def calculate_percentage_change(current, previous):
            if previous is None or previous == 0:
                return 100.0 if current and current > 0 else 0.0
            if current is None:
                return -100.0
            return round(((float(current) - float(previous)) / float(previous)) * 100, 2)
        
        current_distributed = current_totals['total_distributed'] or Decimal('0')
        current_wallets = current_totals['total_wallets'] or 0
        prev_distributed = prev_totals['total_distributed'] or Decimal('0')
        prev_wallets = prev_totals['total_wallets'] or 0
        
        return Response({
            "period": period,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "current_period": {
                "total_distributed": current_distributed,
                "total_distributions": current_distributions_count,
                "total_wallets_rewarded": current_wallets
            },
            "previous_period": {
                "total_distributed": prev_distributed,
                "total_distributions": prev_distributions_count,
                "total_wallets_rewarded": prev_wallets
            },
            "percentage_change": {
                "total_distributed": calculate_percentage_change(current_distributed, prev_distributed),
                "total_distributions": calculate_percentage_change(current_distributions_count, prev_distributions_count),
                "total_wallets_rewarded": calculate_percentage_change(current_wallets, prev_wallets)
            }
        }, status=status.HTTP_200_OK)


class NFTTypeRewardsAPIView(APIView):
    """Get rewards by NFT type with time filtering and percentage changes"""
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('nft_type', openapi.IN_QUERY, description="NFT type (RED, GREEN, BLUE, BLACK, DRAGON, FLAWLESS_DIAMOND)", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('wallet_address', openapi.IN_QUERY, description="Filter by specific wallet address to see user's rewards", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('period', openapi.IN_QUERY, description="Time period filter: 'week', 'month', '6months', 'year', or 'custom'", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date for custom period (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End date for custom period (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False),
        ],
        responses={200: openapi.Response(
            description="Rewards for specific NFT type with percentage changes",
            examples={
                "application/json": {
                    "nft_type": "DRAGON",
                    "period": "month",
                    "start_date": "2026-01-08",
                    "end_date": "2026-02-07",
                    "current_period": {
                        "total_distributed": "50000.000000",
                        "total_distributions": 10,
                        "total_wallets_rewarded": 500
                    },
                    "previous_period": {
                        "total_distributed": "40000.000000",
                        "total_distributions": 8,
                        "total_wallets_rewarded": 400
                    },
                    "percentage_change": {
                        "total_distributed": 25.00,
                        "total_distributions": 25.00,
                        "total_wallets_rewarded": 25.00
                    },
                    "wallet_rewards": [
                        {
                            "transaction_hash": "0xabc123...",
                            "distributed_at": "2026-01-15T10:30:00Z",
                            "per_wallet_amount": "100.000000",
                            "user_reward": "100.000000",
                            "is_sent": True
                        }
                    ]
                }
            }
        ), 400: "Bad Request"}
    )
    def get(self, request):
        """Get rewards for a specific NFT type with time filtering and percentage changes"""
        nft_type = request.query_params.get('nft_type', None)
        wallet_address = request.query_params.get('wallet_address', None)
        
        if not nft_type:
            return Response({
                "error": "nft_type parameter is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        nft_type = nft_type.upper()
        if nft_type not in [choice[0] for choice in NFTType.choices]:
            return Response({
                "error": f"Invalid nft_type. Must be one of: {', '.join([choice[0] for choice in NFTType.choices])}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        elif period == '6months':
            end_date = now
            start_date = now - timedelta(days=180)
            prev_start_date = start_date - timedelta(days=180)
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
            # No period specified - return all time totals for this NFT type
            totals = RewardDistribution.objects.filter(nft_type=nft_type).aggregate(
                total_distributed=Sum('total_amount'),
                total_wallets=Sum('wallet_count')
            )
            total_distributions = RewardDistribution.objects.filter(nft_type=nft_type).count()
            
            response_data = {
                "nft_type": nft_type,
                "total_distributed": totals['total_distributed'] or 0,
                "total_distributions": total_distributions,
                "total_wallets_rewarded": totals['total_wallets'] or 0
            }
            
            # If wallet_address is provided, get that wallet's rewards for this NFT type
            if wallet_address:
                wallet_rewards = PendingReward.objects.filter(
                    wallet_address=wallet_address,
                    nft_type=nft_type
                ).select_related('distribution').order_by('-distribution__distributed_at')
                
                # Group by transaction hash
                grouped_rewards = {}
                for reward in wallet_rewards:
                    tx_hash = reward.distribution.transaction_hash
                    if tx_hash not in grouped_rewards:
                        grouped_rewards[tx_hash] = {
                            'transaction_hash': tx_hash,
                            'distributed_at': reward.distribution.distributed_at,
                            'per_wallet_amount': reward.distribution.per_wallet_amount,
                            'user_reward': Decimal('0'),
                            'is_sent': reward.is_sent,
                            'block_number': reward.distribution.block_number
                        }
                    grouped_rewards[tx_hash]['user_reward'] += reward.dit_amount
                
                response_data['wallet_address'] = wallet_address
                response_data['wallet_rewards'] = list(grouped_rewards.values())
                response_data['total_user_rewards'] = sum(r['user_reward'] for r in grouped_rewards.values())
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        # Get current period totals for this NFT type
        current_totals = RewardDistribution.objects.filter(
            nft_type=nft_type,
            distributed_at__gte=start_date,
            distributed_at__lte=end_date
        ).aggregate(
            total_distributed=Sum('total_amount'),
            total_wallets=Sum('wallet_count')
        )
        current_distributions_count = RewardDistribution.objects.filter(
            nft_type=nft_type,
            distributed_at__gte=start_date,
            distributed_at__lte=end_date
        ).count()
        
        # Get previous period totals for this NFT type
        prev_totals = RewardDistribution.objects.filter(
            nft_type=nft_type,
            distributed_at__gte=prev_start_date,
            distributed_at__lt=prev_end_date
        ).aggregate(
            total_distributed=Sum('total_amount'),
            total_wallets=Sum('wallet_count')
        )
        prev_distributions_count = RewardDistribution.objects.filter(
            nft_type=nft_type,
            distributed_at__gte=prev_start_date,
            distributed_at__lt=prev_end_date
        ).count()
        
        # Calculate percentage changes
        def calculate_percentage_change(current, previous):
            if previous is None or previous == 0:
                return 100.0 if current and current > 0 else 0.0
            if current is None:
                return -100.0
            return round(((float(current) - float(previous)) / float(previous)) * 100, 2)
        
        current_distributed = current_totals['total_distributed'] or Decimal('0')
        current_wallets = current_totals['total_wallets'] or 0
        prev_distributed = prev_totals['total_distributed'] or Decimal('0')
        prev_wallets = prev_totals['total_wallets'] or 0
        
        response_data = {
            "nft_type": nft_type,
            "period": period,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "current_period": {
                "total_distributed": current_distributed,
                "total_distributions": current_distributions_count,
                "total_wallets_rewarded": current_wallets
            },
            "previous_period": {
                "total_distributed": prev_distributed,
                "total_distributions": prev_distributions_count,
                "total_wallets_rewarded": prev_wallets
            },
            "percentage_change": {
                "total_distributed": calculate_percentage_change(current_distributed, prev_distributed),
                "total_distributions": calculate_percentage_change(current_distributions_count, prev_distributions_count),
                "total_wallets_rewarded": calculate_percentage_change(current_wallets, prev_wallets)
            }
        }
        
        # If wallet_address is provided, get that wallet's rewards for this NFT type in the current period
        if wallet_address:
            wallet_rewards = PendingReward.objects.filter(
                wallet_address=wallet_address,
                nft_type=nft_type,
                distribution__distributed_at__gte=start_date,
                distribution__distributed_at__lte=end_date
            ).select_related('distribution').order_by('-distribution__distributed_at')
            
            # Group by transaction hash
            grouped_rewards = {}
            for reward in wallet_rewards:
                tx_hash = reward.distribution.transaction_hash
                if tx_hash not in grouped_rewards:
                    grouped_rewards[tx_hash] = {
                        'transaction_hash': tx_hash,
                        'distributed_at': reward.distribution.distributed_at,
                        'per_wallet_amount': reward.distribution.per_wallet_amount,
                        'user_reward': Decimal('0'),
                        'is_sent': reward.is_sent,
                        'block_number': reward.distribution.block_number
                    }
                grouped_rewards[tx_hash]['user_reward'] += reward.dit_amount
            
            response_data['wallet_address'] = wallet_address
            response_data['wallet_rewards'] = list(grouped_rewards.values())
            response_data['total_user_rewards'] = sum(r['user_reward'] for r in grouped_rewards.values())
        
        return Response(response_data, status=status.HTTP_200_OK)


class AllNFTTypesRewardsAPIView(APIView):
    """Get rewards for all NFT types with time filtering and percentage changes"""
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('period', openapi.IN_QUERY, description="Time period filter: 'week', 'month', '6months', 'year', or 'custom'", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date for custom period (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End date for custom period (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, required=False),
        ],
        responses={200: openapi.Response(
            description="Rewards breakdown by all NFT types",
            examples={
                "application/json": {
                    "period": "month",
                    "start_date": "2026-01-08",
                    "end_date": "2026-02-07",
                    "nft_types": {
                        "RED": {
                            "current_period": {"total_distributed": "10000.00", "total_distributions": 5, "total_wallets_rewarded": 100},
                            "previous_period": {"total_distributed": "8000.00", "total_distributions": 4, "total_wallets_rewarded": 80},
                            "percentage_change": {"total_distributed": 25.00, "total_distributions": 25.00, "total_wallets_rewarded": 25.00}
                        }
                    }
                }
            }
        )}
    )
    def get(self, request):
        """Get rewards breakdown for all NFT types with percentage changes"""
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
        elif period == '6months':
            end_date = now
            start_date = now - timedelta(days=180)
            prev_start_date = start_date - timedelta(days=180)
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
            # No period specified - return all time totals for all NFT types
            nft_types_data = {}
            for nft_choice in NFTType.choices:
                nft_type = nft_choice[0]
                totals = RewardDistribution.objects.filter(nft_type=nft_type).aggregate(
                    total_distributed=Sum('total_amount'),
                    total_wallets=Sum('wallet_count')
                )
                total_distributions = RewardDistribution.objects.filter(nft_type=nft_type).count()
                
                nft_types_data[nft_type] = {
                    "total_distributed": totals['total_distributed'] or 0,
                    "total_distributions": total_distributions,
                    "total_wallets_rewarded": totals['total_wallets'] or 0
                }
            
            return Response({
                "nft_types": nft_types_data
            }, status=status.HTTP_200_OK)
        
        # Calculate percentage changes helper
        def calculate_percentage_change(current, previous):
            if previous is None or previous == 0:
                return 100.0 if current and current > 0 else 0.0
            if current is None:
                return -100.0
            return round(((float(current) - float(previous)) / float(previous)) * 100, 2)
        
        # Get data for all NFT types
        nft_types_data = {}
        for nft_choice in NFTType.choices:
            nft_type = nft_choice[0]
            
            # Current period
            current_totals = RewardDistribution.objects.filter(
                nft_type=nft_type,
                distributed_at__gte=start_date,
                distributed_at__lte=end_date
            ).aggregate(
                total_distributed=Sum('total_amount'),
                total_wallets=Sum('wallet_count')
            )
            current_distributions_count = RewardDistribution.objects.filter(
                nft_type=nft_type,
                distributed_at__gte=start_date,
                distributed_at__lte=end_date
            ).count()
            
            # Previous period
            prev_totals = RewardDistribution.objects.filter(
                nft_type=nft_type,
                distributed_at__gte=prev_start_date,
                distributed_at__lt=prev_end_date
            ).aggregate(
                total_distributed=Sum('total_amount'),
                total_wallets=Sum('wallet_count')
            )
            prev_distributions_count = RewardDistribution.objects.filter(
                nft_type=nft_type,
                distributed_at__gte=prev_start_date,
                distributed_at__lt=prev_end_date
            ).count()
            
            current_distributed = current_totals['total_distributed'] or Decimal('0')
            current_wallets = current_totals['total_wallets'] or 0
            prev_distributed = prev_totals['total_distributed'] or Decimal('0')
            prev_wallets = prev_totals['total_wallets'] or 0
            
            nft_types_data[nft_type] = {
                "current_period": {
                    "total_distributed": current_distributed,
                    "total_distributions": current_distributions_count,
                    "total_wallets_rewarded": current_wallets
                },
                "previous_period": {
                    "total_distributed": prev_distributed,
                    "total_distributions": prev_distributions_count,
                    "total_wallets_rewarded": prev_wallets
                },
                "percentage_change": {
                    "total_distributed": calculate_percentage_change(current_distributed, prev_distributed),
                    "total_distributions": calculate_percentage_change(current_distributions_count, prev_distributions_count),
                    "total_wallets_rewarded": calculate_percentage_change(current_wallets, prev_wallets)
                }
            }
        
        return Response({
            "period": period,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "nft_types": nft_types_data
        }, status=status.HTTP_200_OK)
