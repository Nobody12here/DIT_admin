from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.paginator import InfinitePaginator
from django.template.response import TemplateResponse
from .models import Event
import requests

admin.site.site_header = "Diamond Token Admin"


class EventAdmin(ModelAdmin):
    change_list_template = "admin/event_changelist.html"
    paginator = InfinitePaginator
    show_full_result_count = False

    def changelist_view(self, request, extra_context=None):
        header = {"AccessToken": "8b2be529-0afc-43a2-b8c7-27dfebcfeb81"}
        try:
            response = requests.get(
                "https://api-community-diamond-club.io/api/admin/events/",
                headers=header,
            )
            data = response.json()["data"]["eventDetails"]
        except Exception:
            data = []

        # Build table rows
        table_data = []
        for index, item in enumerate(data):
            title = item.get("title")
            link = item.get("link")
            isActive = item.get("isActive")
            time = item.get("time")
            table_data.append([index + 1, title, time, link, isActive])

        context = {
            "opts": self.model._meta,
            "title": "Community Events",
            "table": {
                "headers": [
                    "ID",
                    "Title",
                    "Time",
                    "Link",
                    "Is Active",
                ],
                "rows": table_data,
            },
            **self.admin_site.each_context(request),
        }

        return TemplateResponse(request, self.change_list_template, context)


admin.site.register(Event, EventAdmin)
