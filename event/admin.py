from django.contrib import admin
from unfold.admin import ModelAdmin
# Register your models here.
class EventAdmin(ModelAdmin):
    change_list_template = '/admin/event_changelist'