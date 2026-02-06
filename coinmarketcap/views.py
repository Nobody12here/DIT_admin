from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import TokenSupplySerializer
from decimal import Decimal
from web3 import Web3
import logging

logger = logging.getLogger(__name__)

# Constants
TOTAL_SUPPLY = Decimal('100000000')  # 100 million DIT tokens
DIT_TOKEN_ADDRESS = '0xbfa362937BFD11eC22a023aBF83B6dF4E5E303d4'

# Excluded wallet addresses (team wallets, treasury, etc.)
EXCLUDED_WALLETS = [
    '0x10B5F02956d242aB770605D59B7D27E51E45774C',
    '0x1d64FD1e4eB9Df7C75Ad4B4DAe6A23aa8C4B5fe8',
    '0x9d921234C93914aF8712682E0C21241c1e179cBD',
    '0xA1179097b0424e9A7A59DB713692278606b904c1',
    '0x820Aa5a602bF939e633AEe38D63A13E2830D85a9',
    '0x0CD0468e488AA9F316D5bd082Ce558005e7bfF15',
]

# ERC-20 ABI for balanceOf function
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


class TokenSupplyAPIView(APIView):
    """
    API endpoint for CoinMarketCap to fetch token supply information.
    Returns total supply and circulating supply of DIT tokens.
    """
    
    @swagger_auto_schema(
        operation_description="Get total supply and circulating supply of DIT tokens for CoinMarketCap",
        responses={
            200: TokenSupplySerializer(),
            500: "Internal Server Error"
        }
    )
    def get(self, request):
        """
        Get token supply information.
        Circulating supply = Total supply - Sum of excluded wallet balances
        """
        try:
            # Initialize Web3 with BSC mainnet RPC
            # Using public BSC RPC endpoint
            w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org'))
            
            if not w3.is_connected():
                logger.error("Failed to connect to BSC network")
                return Response(
                    {"error": "Failed to connect to blockchain network"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Create contract instance
            token_contract = w3.eth.contract(
                address=Web3.to_checksum_address(DIT_TOKEN_ADDRESS),
                abi=ERC20_ABI
            )
            
            # Get token decimals
            try:
                decimals = token_contract.functions.decimals().call()
            except Exception as e:
                logger.warning(f"Failed to get decimals, using default 18: {e}")
                decimals = 18
            
            # Get balances of excluded wallets
            total_excluded_balance = Decimal('0')
            
            for wallet_address in EXCLUDED_WALLETS:
                try:
                    checksum_address = Web3.to_checksum_address(wallet_address)
                    balance_wei = token_contract.functions.balanceOf(checksum_address).call()
                    balance = Decimal(balance_wei) / Decimal(10 ** decimals)
                    total_excluded_balance += balance
                    logger.info(f"Wallet {wallet_address}: {balance} DIT")
                except Exception as e:
                    logger.error(f"Error fetching balance for {wallet_address}: {e}")
                    # Continue with other wallets even if one fails
                    continue
            
            # Calculate circulating supply
            circulating_supply = TOTAL_SUPPLY - total_excluded_balance
            
            # Ensure circulating supply doesn't go negative
            if circulating_supply < 0:
                circulating_supply = Decimal('0')
            
            response_data = {
                'total_supply': TOTAL_SUPPLY,
                'circulating_supply': circulating_supply,
                'excluded_wallets_balance': total_excluded_balance,
                'max_supply': TOTAL_SUPPLY,  # For CoinMarketCap compatibility
            }
            
            serializer = TokenSupplySerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in TokenSupplyAPIView: {str(e)}")
            return Response(
                {"error": f"Failed to fetch token supply data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TotalSupplyAPIView(APIView):
    """
    Simple endpoint that returns only the total supply.
    CoinMarketCap compatible endpoint.
    """
    
    @swagger_auto_schema(
        operation_description="Get total supply of DIT tokens (100 million)",
        responses={200: openapi.Response(
            description="Total supply",
            examples={"application/json": "100000000"}
        )}
    )
    def get(self, request):
        """Return total supply as a plain number"""
        return Response(str(TOTAL_SUPPLY), status=status.HTTP_200_OK)


class CirculatingSupplyAPIView(APIView):
    """
    Simple endpoint that returns only the circulating supply.
    CoinMarketCap compatible endpoint.
    """
    
    @swagger_auto_schema(
        operation_description="Get circulating supply of DIT tokens (total supply minus excluded wallets)",
        responses={
            200: openapi.Response(
                description="Circulating supply",
                examples={"application/json": "85000000.50"}
            ),
            500: "Internal Server Error"
        }
    )
    def get(self, request):
        """Return circulating supply as a plain number"""
        try:
            # Initialize Web3 with BSC mainnet RPC
            w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org'))
            
            if not w3.is_connected():
                logger.error("Failed to connect to BSC network")
                return Response(
                    {"error": "Failed to connect to blockchain network"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Create contract instance
            token_contract = w3.eth.contract(
                address=Web3.to_checksum_address(DIT_TOKEN_ADDRESS),
                abi=ERC20_ABI
            )
            
            # Get token decimals
            try:
                decimals = token_contract.functions.decimals().call()
            except Exception as e:
                logger.warning(f"Failed to get decimals, using default 18: {e}")
                decimals = 18
            
            # Get balances of excluded wallets
            total_excluded_balance = Decimal('0')
            
            for wallet_address in EXCLUDED_WALLETS:
                try:
                    checksum_address = Web3.to_checksum_address(wallet_address)
                    balance_wei = token_contract.functions.balanceOf(checksum_address).call()
                    balance = Decimal(balance_wei) / Decimal(10 ** decimals)
                    total_excluded_balance += balance
                except Exception as e:
                    logger.error(f"Error fetching balance for {wallet_address}: {e}")
                    continue
            
            # Calculate circulating supply
            circulating_supply = TOTAL_SUPPLY - total_excluded_balance
            
            # Ensure circulating supply doesn't go negative
            if circulating_supply < 0:
                circulating_supply = Decimal('0')
            
            return Response(str(circulating_supply), status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in CirculatingSupplyAPIView: {str(e)}")
            return Response(
                {"error": f"Failed to fetch circulating supply: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
