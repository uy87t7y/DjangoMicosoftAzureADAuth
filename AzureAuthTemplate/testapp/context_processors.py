def azure_user_context(request):
    """Expose azure user to templates as `azure_user` if available in session or request."""
    import json

    expected_keys = ('user_id', 'name', 'first_name', 'email', 'officeLocation', 'office_location', 'position', 'roles', 'graph_token')

    def _force_dict(obj):
        # Always return a plain dict with expected keys
        if obj is None:
            return None
        # If already a dict
        if isinstance(obj, dict):
            out = obj.copy()
        else:
            # Pydantic v1
            if hasattr(obj, 'dict') and callable(obj.dict):
                try:
                    out = obj.dict()
                except Exception:
                    out = None
            else:
                out = None
            # Pydantic v2
            if out is None and hasattr(obj, 'model_dump') and callable(obj.model_dump):
                try:
                    out = obj.model_dump()
                except Exception:
                    out = None
            # As last resort, extract attributes
            if out is None:
                out = {}
                for k in expected_keys:
                    try:
                        v = getattr(obj, k)
                    except Exception:
                        v = None
                    out[k] = v

        # Normalize keys
        if 'office_location' not in out and 'officeLocation' in out:
            out['office_location'] = out.get('officeLocation')
        if 'officeLocation' not in out and 'office_location' in out:
            out['officeLocation'] = out.get('office_location')

        # Ensure roles is a list
        roles = out.get('roles') or []
        if isinstance(roles, str):
            try:
                roles = json.loads(roles)
            except Exception:
                roles = [roles]
        out['roles'] = roles

        # Ensure all expected keys exist
        for k in expected_keys:
            if k not in out:
                out[k] = None

        return out

    # Determine raw source
    raw = None
    if hasattr(request, 'azure_user') and request.azure_user:
        raw = request.azure_user
    else:
        sess = request.session.get('user')
        if sess:
            raw = sess
        elif hasattr(request, 'user') and request.user.is_authenticated:
            # build minimal mapping from Django user
            u = request.user
            raw = {
                'user_id': getattr(u, 'user_id', None),
                'name': getattr(u, 'get_full_name', lambda: str(u))() if hasattr(u, 'get_full_name') else str(u),
                'first_name': getattr(u, 'first_name', None),
                'email': getattr(u, 'email', None),
                'officeLocation': getattr(u, 'officeLocation', None) or getattr(u, 'office_location', None),
                'office_location': getattr(u, 'office_location', None) or getattr(u, 'officeLocation', None),
                'position': getattr(u, 'position', None),
                'roles': getattr(u, 'roles', []),
                'graph_token': None,
            }

    azure_user = _force_dict(raw) if raw is not None else None

    return {'azure_user': azure_user}
