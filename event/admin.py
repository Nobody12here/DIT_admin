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
    image = forms.ImageField(required=False)
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
            event = next((e for e in all_events if e.get("_id") == event_id), None)
            if not event:
                raise Exception(f"Event with ID {event_id} not found")
        except Exception as e:
            messages.error(request, f"Failed to load event: {e}")
            return redirect("..")

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
                "current_image": event.get(
                    "imagePath", ""
                ),  # Pass current image to template
                **self.admin_site.each_context(request),
            }
            return TemplateResponse(request, self.change_form_template, context)

        elif request.method == "POST":
            update_url = (
                f"https://api-community-diamond-club.io/api/admin/event/{event_id}/"
            )
            form = EventForm(
                request.POST, request.FILES
            )  # Important: include request.FILES
            if form.is_valid():
                try:
                    patch_data = {
                        "title": form.cleaned_data["title"],
                        "time": form.cleaned_data["time"],
                        "link": form.cleaned_data["link"],
                        "isActive": bool(form.cleaned_data["isActive"]),
                    }
                    files = {}
                    # Handle file upload
                    if "image" in request.FILES:
                        image_file = request.FILES['image']
                        files['image'] = (image_file.name, image_file, image_file.content_type)
                        patch_data['isActive'] = 'true' if patch_data['isActive'] else 'false'
                        # For file upload, you typically need to send as multipart form data
                        response = requests.patch(
                            update_url, data=patch_data,files=files, headers=headers
                        )

                        if response.status_code == 200:
                            messages.success(request, "Event updated successfully!")
                            return redirect("../../")
                        else:
                            error_msg = response.json().get('message', 'Update failed')
                            print(patch_data["isActive"])
                            raise Exception(error_msg)
                    else:
                        # If no new image, just send the data
                        requests.patch(update_url, json=patch_data, headers=headers)

                    messages.success(request, "Event updated successfully.")
                    return redirect("../../")
                except Exception as e:
                    messages.error(request, f"Failed to update event: {e}")

            context = {
                "opts": self.model._meta,
                "title": f"Edit Event #{event_id}",
                "form": form,
                "current_image": event.get("imagePath", ""),
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
            title = item.get("title")
            link = item.get("link")
            image = item.get("imagePath", "")
            isActive = item.get("isActive")
            time = item.get("time")
            table_data.append(
                [
                    f'<a href="{event_update_url}">{index + 1}</a>',
                    title,
                    time,
                    image,
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
                    "Image",
                    "Link",
                    "Is Active",
                ],
                "rows": table_data,
            },
            **self.admin_site.each_context(request),
        }

        return TemplateResponse(request, self.change_list_template, context)


admin.site.register(Event, EventAdmin)
