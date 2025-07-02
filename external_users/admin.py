from django.contrib import admin
from unfold.admin import ModelAdmin
from django.template.response import TemplateResponse
from django.urls import path
from .models import ExternalUser
import requests


from django.template.response import TemplateResponse
from .models import ExternalUser

class ExternalUserAdmin(ModelAdmin):
    change_list_template = "admin/external_users_changelist.html"

    def changelist_view(self, request, extra_context=None):
        header = {"AccessToken": "8b2be529-0afc-43a2-b8c7-27dfebcfeb81"}
        try:
            response = requests.get(
                "https://api-community-diamond-club.io/api/admin/users", headers=header
            )
            data = response.json()["data"]["userDetailsWithTokenCount"]
        except Exception as e:
            data = []

        table_data = []
        for item in data:
            table_data.append([
                item.get("displayName", "-"),
                item.get("email", "-"),
                item.get("walletDetails", {}).get("walletAddress", "-"),
                item.get("ditTokenBalance", "0"),
            ])

        table = {
            "headers": ["Display Name", "Email", "Wallet Address", "DIT Token Balance"],
            "rows": table_data,
        }

        context = {
            "opts": self.model._meta,
            "title": "External Users",
            "table": table,
            **self.admin_site.each_context(request),
        }

        return TemplateResponse(request, self.change_list_template, context)



admin.site.register(ExternalUser, ExternalUserAdmin)
