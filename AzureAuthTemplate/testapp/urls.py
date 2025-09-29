from django.urls import path, include
from .views import home, azure_protected_view

urlpatterns = [
    path('', home, name='home'),
    path('azure-protected/', azure_protected_view, name='azure_protected'),
]
