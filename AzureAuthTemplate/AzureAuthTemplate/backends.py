from azure_auth.backends import AzureBackend
from django.contrib.auth import get_user_model
from django.conf import settings
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

def safe_string(s):
    """Safely convert and escape string values"""
    if type(s) != str:
        try:
            s = str(s)
        except:
            return s
    return s.replace('&', '&amp;') \
            .replace('<', '&lt;') \
            .replace('>', '&gt;') \
            .replace("'", '_')


class CustomAzureBackend(AzureBackend):
    """
    Custom Azure authentication backend that extends AzureBackend
    to store user attributes in session under 'user' key for compatibility
    with existing code structure.
    """
    
    def authenticate(self, request, token=None, **kwargs):
        """
        Override authenticate method to store user data in session
        """
        # Call parent authenticate method first
        user = super().authenticate(request, token=token, **kwargs)
        
        if user and token:
            # Get all user attributes similar to how the library does it
            from azure_auth.handlers import AuthHandler
            handler = AuthHandler(request)
            
            # Get Azure user profile from Microsoft Graph API
            azure_user = handler._get_azure_user(token["access_token"])
            
            # Get extra fields if configured
            extra_fields = {}
            azure_auth_settings = getattr(settings, 'AZURE_AUTH', {})
            if fields := azure_auth_settings.get("EXTRA_FIELDS"):
                extra_fields = handler._get_azure_user(token["access_token"], fields=fields)
            
            # Combine all attributes (same as in the library's authenticate method)
            id_token_claims = token.get('id_token_claims', {})
            attributes = {**azure_user, **extra_fields, **id_token_claims}
                        
            # Get roles from the combined attributes
            roles = []
            group_attribute = azure_auth_settings.get('GROUP_ATTRIBUTE', 'roles')
            if group_attribute in attributes:
                roles = [role for role in attributes.get('roles', []) if role]  # Filter out None values
            
            # Store user data in session using the combined attributes
            self._store_user_in_session(request, attributes, roles, token.get('access_token'))
            
        return user
    
    def _store_user_in_session(self, request, user_claims, roles, access_token=None):
        """
        Store user attributes in session under 'user' key
        """
        try:
            logger.info(f'Storing user in session: {user_claims.get("name", user_claims.get("displayName", "Unknown"))}, '
                  f'officeLocation: {user_claims.get("officeLocation", "Unknown")}')
            
            # Get hotel information based on office location
            office_location = safe_string(user_claims.get('officeLocation', ''))
            user_claims['officeLocation'] = office_location
                
            # Map the Azure token claims to the expected session structure
            user_email = user_claims.get('mail') or user_claims.get('userPrincipalName') or user_claims.get('upn', '')
            
            # Store user data in session with the same structure as your existing code
            request.session['user'] = {
                'is_authenticated': True,
                'name': safe_string(user_claims.get('name', user_claims.get('displayName', ''))),
                'first_name': safe_string(user_claims.get('givenName', user_claims.get('givenName', ''))),
                'email': safe_string(user_email),
                'officeLocation': office_location,
                'position': safe_string(user_claims.get('jobTitle', '')),
                'user_id': safe_string(user_claims.get('oid', user_claims.get('sub', ''))),
                'roles': roles or [],
                'graph_token': access_token,
            }

            # Also persist/update an AzureUser DB model for programmatic access
            try:
                from testapp.models import AzureUser

                AzureUser.objects.update_or_create(
                    user_id=request.session['user']['user_id'],
                    defaults={
                        'name': request.session['user']['name'],
                        'first_name': request.session['user']['first_name'],
                        'email': request.session['user']['email'],
                        'office_location': request.session['user']['officeLocation'],
                        'position': request.session['user']['position'],
                        'roles': request.session['user']['roles'],
                        'graph_token': request.session['user']['graph_token'],
                        'last_seen': timezone.now(),
                    }
                )
            except Exception:
                logger.exception('Failed to create/update AzureUser model')
        except Exception as e:
            logger.error(f"Error storing user in session: {e}")
