from django.urls import path
from .views import DonationAPIView, DonationDetailAPIView

urlpatterns = [
    path("", DonationAPIView.as_view(), name="donation-list"),
    path("<int:pk>/", DonationDetailAPIView.as_view(), name="donation-detail"),
]
