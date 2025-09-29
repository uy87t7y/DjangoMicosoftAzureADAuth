from django.shortcuts import render
from azure_auth.decorators import azure_auth_required
import logging

logger = logging.getLogger(__name__)

# Create your views here.
def home(request):
    """Home page view - accessible to all users"""
    # Try to access azure user attached by middleware
    azure_user = getattr(request, 'azure_user', None)
    azure_user_db = getattr(request, 'azure_user_db', None)
    logger.info('Home view - azure_user: %s', azure_user)
    return render(request, "home.html", {
        "page_title": "Azure Auth Demo - Home",
        "message": "Welcome to the Azure AD Authentication Demo Application",
        'azure_user': azure_user,
        'azure_user_db': azure_user_db,
    })

@azure_auth_required
def azure_protected_view(request):
    """Protected view - requires Azure AD authentication"""
    azure_user = getattr(request, 'azure_user', None)
    azure_user_db = getattr(request, 'azure_user_db', None)
    logger.info('Protected view - azure_user: %s', azure_user)
    return render(request, "protected.html", {
        "page_title": "Azure Auth Demo - Protected Area",
        "message": "You have successfully accessed the protected area",
        'azure_user': azure_user,
        'azure_user_db': azure_user_db,
    })