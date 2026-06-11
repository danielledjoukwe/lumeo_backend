"""
Reusable email utility for Lumeo.

Usage:
    from config.utils.email import send_email

    send_email(
        template='auth/email/verification_code.html',
        context={'code': '123456', 'user': user},
        subject='Your verification code',
        recipient=user.email,
    )
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_email(template: str, context: dict, subject: str, recipient: str | list) -> bool:
    """
    Send an HTML email rendered from a Django template.

    Args:
        template:   Path to the HTML template (relative to templates/).
        context:    Dict passed to the template renderer.
        subject:    Email subject line.
        recipient:  A single email address string or a list of addresses.

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    if isinstance(recipient, str):
        recipient = [recipient]

    # Always inject APP_NAME so every template can use it
    context.setdefault('APP_NAME', settings.APP_NAME)
    context.setdefault('SITE_URL', settings.SITE_URL)

    html_body  = render_to_string(template, context)
    plain_body = strip_tags(html_body)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient,
    )
    msg.attach_alternative(html_body, 'text/html')

    try:
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("send_email failed: %s", e, exc_info=True)
        return False
