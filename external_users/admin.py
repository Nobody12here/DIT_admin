from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.paginator import InfinitePaginator
from django.template.response import TemplateResponse
from .models import ExternalUser
import requests

admin.site.site_header = "Diamond Token Admin"

class ExternalUserAdmin(ModelAdmin):
    change_list_template = "admin/external_users_changelist.html"
    list_filter = ["email"]  # Add filters you want to support
    paginator = InfinitePaginator
    show_full_result_count = False
    
    def get_filters_params(self, params):
        """Extract filter parameters from request GET params"""
        filters = {}
        if 'email__icontains' in params:
            filters['email__icontains'] = params['email__icontains'].lower()
        if 'wallet_provider__icontains' in params:
            filters['wallet_provider__icontains'] = params['wallet_provider__icontains'].lower()
        return filters


    def changelist_view(self, request, extra_context=None):
        header = {"AccessToken": "8b2be529-0afc-43a2-b8c7-27dfebcfeb81"}
        try:
            response = requests.get(
                "https://api-community-diamond-club.io/api/admin/users?limit=100",
                headers=header,
            )
            all_data = response.json()["data"]["userDetailsWithTokenCount"]
        except Exception:
            all_data = []

        # Get filter parameters
        filters = self.get_filters_params(request)
        
        # Apply filters
        filtered_data = []
        for index, item in enumerate(all_data):
            wallet_details = item.get("walletDetails", {})
            nft_details = item.get("membershipNftsWithCounts", {})
            
            wallet_address = wallet_details.get("walletAddress", "-") if isinstance(wallet_details, dict) else item.get("walletAddress", "-")
            wallet_provider = wallet_details.get("walletProvider", "-").lower() if isinstance(wallet_details, dict) else "-"
            email = item.get("email", "-")
            email = email.lower() if email else "-"
            # Check filters
            if filters.get('email__icontains') and filters['email__icontains'] not in email:
                continue
            if filters.get('wallet_provider__icontains') and filters['wallet_provider__icontains'] not in wallet_provider:
                continue
                
            filtered_data.append({
                "id": index + 1,
                "display_name": item.get("displayName", "-"),
                "email": email,
                "wallet_address": wallet_address or "-",
                "dit_token_balance": item.get("ditTokenBalance", "0"),
                "wallet_provider": wallet_provider.capitalize(),
                "flawless": nft_details.get("Flawless Diamonds", 0),
                "red": nft_details.get("Red Diamonds", 0),
                "blue": nft_details.get("Blue Diamonds", 0),
                "green": nft_details.get("Green Diamonds", 0),
                "black": nft_details.get("Black Diamonds", 0),
            })

        context = {
            "opts": self.model._meta,
            "title": "Community Members",
            "striped": 1,
            "card": 1,
            "height": 600,
            'sortable': True,
            'has_filters': True,
            "table_rows": filtered_data,
            "table_headers": [
                "ID", "Display Name", "Email", "Wallet Address", 
                "DIT Token Balance", "Wallet Provider",
                "Flawless", "Red", "Blue", "Green", "Black"
            ],
            **self.admin_site.each_context(request),
        }

        return TemplateResponse(request, self.change_list_template, context)


admin.site.register(ExternalUser, ExternalUserAdmin)