from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.paginator import InfinitePaginator
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django import forms
from django.template.response import TemplateResponse
from .models import Event
import requests

admin.site.site_header = "Diamond Token Admin"


class EventForm(forms.Form):
    title = forms.CharField()
    time = forms.CharField()
    link = forms.URLField(required=False)
    isActive = forms.BooleanField(required=False)


class EventAdmin(ModelAdmin):
    change_list_template = "admin/event_changelist.html"
    change_form_template = "admin/event_update.html"
    paginator = InfinitePaginator
    show_full_result_count = False

    def get_urls(self):
        default_urls = super().get_urls()
        custom_urls = [
            path(
                "edit/<str:event_id>/",
                self.admin_site.admin_view(self.edit_event_view),
                name="edit_event",
            ),
        ]
        return custom_urls + default_urls

    def edit_event_view(self, request, event_id):
        list_api_url = "https://api-community-diamond-club.io/api/admin/events/"
        headers = {"AccessToken": "8b2be529-0afc-43a2-b8c7-27dfebcfeb81"}

        try:
            response = requests.get(list_api_url, headers=headers)
            all_events = response.json()["data"]["eventDetails"]

            # Find the event with the matching _id
            event = next((e for e in all_events if e.get("_id") == event_id), None)

            if not event:
                raise Exception(f"Event with ID {event_id} not found")

        except Exception as e:
            print("❌ Could not fetch event data:", e)
            messages.error(request, f"Failed to load event: {e}")
            return redirect("..")

        # GET request — show the form
        if request.method == "GET":
            form = EventForm(
                initial={
                    "title": event.get("title", ""),
                    "time": event.get("time", ""),
                    "link": event.get("link", ""),
                    "isActive": event.get("isActive", False),
                }
            )
            context = {
                "opts": self.model._meta,
                "title": f"Edit Event #{event_id}",
                "form": form,
                **self.admin_site.each_context(request),    
            }
            return TemplateResponse(request, self.change_form_template, context)

        # POST request — PATCH to update
        elif request.method == "POST":
            form = EventForm(request.POST)
            if form.is_valid():
                try:
                    patch_data = {
                        "title": form.cleaned_data["title"],
                        "time": form.cleaned_data["time"],
                        "link": form.cleaned_data["link"],
                        "isActive": form.cleaned_data["isActive"],
                    }
                    # Send PATCH request — assuming this endpoint works
                    update_url = f"https://api-community-diamond-club.io/api/admin/event/{event_id}/"
                    requests.patch(update_url, json=patch_data, headers=headers)

                    messages.success(request, "Event updated successfully.")
                    return redirect("../../")
                except Exception as e:
                    messages.error(request, f"Failed to update event: {e}")

            context = {
                "opts": self.model._meta,
                "title": f"Edit Event #{event_id}",
                "form": form,
                **self.admin_site.each_context(request),
            }
            return TemplateResponse(request, self.change_form_template, context)

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
            event_id = item.get("_id")
            event_update_url = reverse("admin:edit_event", args=[event_id])
            print(event_update_url)
            title = item.get("title")
            link = item.get("link")
            isActive = item.get("isActive")
            time = item.get("time")
            table_data.append(
                [
                    f'<a href="{event_update_url}">{index + 1}</a>',
                    title,
                    time,
                    link,
                    isActive,
                ]
            )

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
