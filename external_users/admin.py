from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.paginator import InfinitePaginator
from django.template.response import TemplateResponse
from .models import ExternalUser
import requests

admin.site.site_header = "Diamond Token Admin"


class ExternalUserAdmin(ModelAdmin):
    change_list_template = "admin/external_users_changelist.html"
    paginator = InfinitePaginator
    show_full_result_count = False

    def changelist_view(self, request, extra_context=None):
        header = {"AccessToken": "8b2be529-0afc-43a2-b8c7-27dfebcfeb81"}
        try:
            response = requests.get(
                "https://api-community-diamond-club.io/api/admin/users?limit=100",
                headers=header,
            )
            data = response.json()["data"]["userDetailsWithTokenCount"]
        except Exception:
            data = []
        #Sorting Logic
        sort_field = request.GET.get("sort")
        order = request.GET.get("order", "asc")
        # Build table rows
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
                    wallet_address or "-",
                    item.get("ditTokenBalance", "0"),
                    wallet_provider,
                    nft_details.get("Flawless Diamonds"),
                    nft_details.get("Red Diamonds"),
                    nft_details.get("Blue Diamonds"),
                    nft_details.get("Green Diamonds"),
                    nft_details.get("Black Diamonds"),
                ]
            )
        sort_map = {
        "Flawless": 6,
        "Red": 7,
        "Blue": 8,
        "Green": 9,
        "Black": 10,
        }
        if sort_field in sort_map:
            col_index = sort_map[sort_field]
            table_data.sort(key=lambda x: x[col_index], reverse=(order == "desc"))

        context = {
            "opts": self.model._meta,
            "title": "Community Members",
            "table": {
                "headers": [
                    "ID",
                    "Display Name",
                    "Email",
                    "Wallet Address",
                    "DIT Token Balance",
                    "Wallet Provider",
                    "Flawless",
                    "Red",
                    "Blue",
                    "Green",
                    "Black",
                ],
                "rows": table_data,
            },
            **self.admin_site.each_context(request),
        }

        return TemplateResponse(request, self.change_list_template, context)


admin.site.register(ExternalUser, ExternalUserAdmin)
