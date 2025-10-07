from django.urls import path
from membership.views import MembershipAPIView

urlpatterns = [
    path("", MembershipAPIView.as_view(), name="membership"),
]
