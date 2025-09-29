from django.utils.deprecation import MiddlewareMixin
from .models import AzureUser
from .schemas import AzureUserSchema

class AzureUserMiddleware(MiddlewareMixin):
    """Attach an `azure_user` attribute to the request for quick access in views.

    The middleware looks for session['user'] (populated by the custom backend)
    and, if present, will hydrate a Pydantic model and attach it to request.azure_user.
    """
    def process_request(self, request):
        sess = request.session.get('user')
        if not sess:
            request.azure_user = None
            return None

        # Convert roles to list if stored as string
        roles = sess.get('roles') or []
        if isinstance(roles, (str,)):
            try:
                import json
                roles = json.loads(roles)
            except Exception:
                roles = [roles]

        payload = {
            'user_id': sess.get('user_id'),
            'name': sess.get('name'),
            'first_name': sess.get('first_name'),
            'email': sess.get('email'),
            'office_location': sess.get('officeLocation'),
            'position': sess.get('position'),
            'roles': roles,
            'graph_token': sess.get('graph_token'),
        }

        try:
            # Validate and attach Pydantic model
            request.azure_user = AzureUserSchema(**payload)
        except Exception:
            # Best-effort: still attach raw payload
            request.azure_user = payload

        # Optionally, hydrate from DB if available
        try:
            db_user = AzureUser.objects.filter(user_id=payload['user_id']).first()
            if db_user:
                request.azure_user_db = db_user
        except Exception:
            request.azure_user_db = None

        return None
