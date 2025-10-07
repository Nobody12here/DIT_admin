from django.contrib import admin
from membership.models import Membership
from unfold.admin import ModelAdmin

admin.site.site_header = "DIORA membership Admin"


@admin.register(Membership)
class MembershipAdmin(ModelAdmin):
    list_display = (
        "id",
        "receiver_address",
        "crypto_currency",
        "usdt_amount",
        "purchase_date",
        "membership_added",
    )

    list_filter = (
        "crypto_currency",
        "membership_added",
        "purchase_date",
    )  # Optional filters on sidebar
    search_fields = ("receiver_address", "crypto_currency")  # Optional search bar
    ordering = ("-purchase_date",)  # Most recent purchases first
    list_editable = ("membership_added",)
