from django.contrib import admin
from .models import Donation
from unfold.admin import ModelAdmin

admin.site.site_header = "DRAGON Donation Admin"


@admin.register(Donation)
class MembershipAdmin(ModelAdmin):
    list_display = (
        "id",
        "receiver_address",
        "dit_amount",
        "usdt_amount",
        "donated_at",
        "has_dragon",
        "dragon_delivered",
    )

    list_filter = (
        "receiver_address",
        "has_dragon",
        "dragon_delivered",
        "donated_at",
    )  # Optional filters on sidebar
    search_fields = ("receiver_address", "dit_amount", "usdt_amount")  # Optional search bar
    ordering = ("-donated_at",)  # Most recent purchases first
    list_editable = ("has_dragon", "dragon_delivered", "usdt_amount")
