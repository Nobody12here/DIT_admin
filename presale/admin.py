from django.contrib import admin
from presale.models import Presale
from unfold.admin import ModelAdmin

admin.site.site_header = "Diamond Token Admin"


@admin.register(Presale)
class PresaleAdmin(ModelAdmin):
    list_display = (
        "id",
        "receiver_address",
        "crypto_currency",
        "dit_amount",
        "usdt_amount",
        "purchase_date",
        "tokens_delivered",
    )

    list_filter = (
        "crypto_currency",
        "tokens_delivered",
        "purchase_date",
    )  # Optional filters on sidebar
    search_fields = ("receiver_address", "crypto_currency")  # Optional search bar
    ordering = ("-purchase_date",)  # Most recent purchases first
    list_editable = ("tokens_delivered",)
