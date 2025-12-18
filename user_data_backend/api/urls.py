from django.urls import path
from .views import health
from .user_data_views import user_data

urlpatterns = [
    path('health/', health, name='Health'),
    path('user-data/', user_data, name='UserData'),
]
