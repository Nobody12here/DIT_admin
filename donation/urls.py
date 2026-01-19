from django.urls import path
from .views import DonationAPIView

urlpatterns = [
    path("", DonationAPIView.as_view(), name="donation"),
]
