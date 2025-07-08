from django.contrib import admin
from unfold.admin import ModelAdmin
from django.template.response import TemplateResponse
from .models import ExternalUser
import requests

admin.site.site_header = "Diamond Token Admin"

class ExternalUserAdmin(ModelAdmin):
    change_list_template = "admin/external_users_changelist.html"

    def changelist_view(self, request, extra_context=None):
        header = {"AccessToken": "8b2be529-0afc-43a2-b8c7-27dfebcfeb81"}
        try:
            response = requests.get(
                "https://api-community-diamond-club.io/api/admin/users?limit=100",
                headers=header,
            )
            data = response.json()["data"]["userDetailsWithTokenCount"]
            print(data)
        except Exception:
            data = []
        search_query = request.GET.get("search", "").lower().strip()
        if search_query:

            def matches_search(item):
                email = item.get("email", "")
                wallet_details = item.get("walletDetails", {})
                wallet_address = (
                    wallet_details.get("walletAddress", "")
                    if isinstance(wallet_details, dict)
                    else item.get("walletAddress", "")
                )
                return (email and search_query in email.lower()) or (
                    wallet_address and search_query in wallet_address.lower()
                )

            data = list(filter(matches_search, data))

        table_data = []
        for index, item in enumerate(data):
            wallet_details = item.get("walletDetails")
            nft_details = item.get("membershipNftsWithCounts")
            if isinstance(wallet_details, dict):
                wallet_address = wallet_details.get("walletAddress", "-")
                wallet_provider = wallet_details.get("walletProvider", "-")
            else:
                wallet_address = item.get("walletAddress", "-")
            table_data.append(
                [
                    index + 1,
                    item.get("displayName", "-"),
                    item.get("email", "-"),
                    wallet_address if wallet_address else "-",
                    item.get("ditTokenBalance", "0"),
                    wallet_provider,
                    nft_details.get("Flawless Diamonds"),
                    nft_details.get("Red Diamonds"),
                    nft_details.get("Blue Diamonds"),
                    nft_details.get("Green Diamonds"),
                    nft_details.get("Black Diamonds"),
                ]
            )

        table = {
            "headers": [
                "ID",
                "Display Name",
                "Email",
                "Wallet Address",
                "DIT Token Balance",
                "Wallet provider",
                "Flawless",
                "Red",
                "Blue",
                "Green",
                "Black",
            ],
            "rows": table_data,
        }

        context = {
            "opts": self.model._meta,
            "title": "Community Members",
            "table": table,
            **self.admin_site.each_context(request),
        }

        return TemplateResponse(request, self.change_list_template, context)


admin.site.register(ExternalUser, ExternalUserAdmin)
