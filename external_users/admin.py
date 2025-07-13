from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.paginator import InfinitePaginator
from django.template.response import TemplateResponse
from .models import ExternalUser
import requests


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

        # Get filter flags from GET
        filter_wallet_provider = request.GET.get("filter_wallet_provider") == "true"
        filter_email = request.GET.get("filter_email") == "true"
        filter_display_name = request.GET.get("filter_display_name") == "true"

        # Filter out items missing the required fields
        filtered_data = []
        for item in data:
            wallet_details = item.get("walletDetails", {})
            wallet_provider = (
                wallet_details.get("walletProvider")
                if isinstance(wallet_details, dict)
                else None
            )
            email = item.get("email")
            display_name = item.get("displayName")

            if filter_wallet_provider and not wallet_provider:
                continue
            if filter_email and not email:
                continue
            if filter_display_name and not display_name:
                continue

            filtered_data.append(item)

        # Build table rows
        table_data = []
        for index, item in enumerate(filtered_data):
            wallet_details = item.get("walletDetails", {})
            wallet_address = (
                wallet_details.get("walletAddress")
                if isinstance(wallet_details, dict)
                else item.get("walletAddress", "-")
            )
            wallet_provider = (
                wallet_details.get("walletProvider")
                if isinstance(wallet_details, dict)
                else "-"
            )
            table_data.append(
                [
                    index + 1,
                    item.get("displayName", "-"),
                    item.get("email", "-"),
                    wallet_address or "-",
                    item.get("ditTokenBalance", "0"),
                    wallet_provider or "-",
                ]
            )

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
                ],
                "rows": table_data,
            },
            "filter_flags": {
                "filter_wallet_provider": filter_wallet_provider,
                "filter_email": filter_email,
                "filter_display_name": filter_display_name,
            },
            **self.admin_site.each_context(request),
        }

        return TemplateResponse(request, self.change_list_template, context)


admin.site.register(ExternalUser, ExternalUserAdmin)
