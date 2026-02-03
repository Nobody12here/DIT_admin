from django.urls import path
from .views import DonationAPIView, DonationDetailAPIView, TotalDonationAPIView

urlpatterns = [
    path("", DonationAPIView.as_view(), name="donation-list"),
    path("total/", TotalDonationAPIView.as_view(), name="donation-total"),
    path("<str:receiver_address>/", DonationDetailAPIView.as_view(), name="donation-detail"),
]
