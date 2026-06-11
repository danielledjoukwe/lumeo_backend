from django.urls import path
from .api_views.auth_views import (
    register_api_view,
    verify_email_api_view,
    resend_verification_api_view,
    login_api_view,
    forgot_password_api_view,
    reset_password_api_view,
    logout_api_view,
)

urlpatterns = [
    path('register/', register_api_view, name='api_register'),
    path('verify-email/', verify_email_api_view, name='api_verify_email'),
    path('resend-verification/', resend_verification_api_view, name='api_resend_verification'),
    path('login/', login_api_view, name='api_login'),
    path('forgot-password/', forgot_password_api_view, name='api_forgot_password'),
    path('reset-password/', reset_password_api_view, name='api_reset_password'),
    path('logout/', logout_api_view, name='api_logout'),
]
