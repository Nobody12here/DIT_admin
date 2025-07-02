from django.urls import path
from .views import ExternalUserAPIView

urlpatterns = [path("", ExternalUserAPIView.as_view(), name="external-users")]
