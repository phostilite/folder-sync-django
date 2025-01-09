from django.urls import path
from .views import SyncConfigurationView

urlpatterns = [
    path('', SyncConfigurationView.as_view(), name='sync_configuration'),
]
