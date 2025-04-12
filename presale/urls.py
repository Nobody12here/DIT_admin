from django.urls import path
from presale.views import PresaleAPIView
urlpatterns = [
    path('presale/', PresaleAPIView.as_view(), name='presale'),
]