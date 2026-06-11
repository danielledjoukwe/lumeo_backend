"""
Role & access check utility.

Usage in any view:

    from config.utils.role_check import check_access

    error = check_access(request, roles=['influencer'])
    if error:
        return error

`roles` is a list of allowed role strings:
    'influencer', 'business', 'administrator'

Pass roles=None (or omit it) to allow any authenticated, active, verified user.

The function always re-fetches the user from the database so stale JWT
payloads (role changed, deactivated, etc.) are caught immediately.
"""

from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()


def check_access(request, roles=None):
    """
    Validates that the authenticated user:
      1. Still exists in the database (not deleted after token was issued).
      2. Is active (is_active=True).
      3. Has a verified email (is_email_verified=True) — staff are exempt.
      4. Has one of the allowed roles (if `roles` is provided).

    Returns None when access is granted.
    Returns a DRF Response with the appropriate error when access is denied,
    so the caller can return it directly.
    """
    try:
        user = User.objects.get(pk=request.user.pk)
    except User.DoesNotExist:
        return Response(
            {"error": "Compte introuvable."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {"error": "Ce compte a été désactivé."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Staff bypass email verification (superusers / admins created via CLI)
    if not user.is_staff and not user.is_email_verified:
        return Response(
            {"error": "Veuillez vérifier votre adresse e-mail."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if roles is not None:
        # Administrators / staff can pass any role-restricted endpoint
        if not user.is_staff and user.role not in roles:
            allowed = " / ".join(roles)
            return Response(
                {"error": f"Accès réservé aux rôles : {allowed}."},
                status=status.HTTP_403_FORBIDDEN,
            )

    # Attach the fresh DB user so views can use it directly
    request._db_user = user
    return None
