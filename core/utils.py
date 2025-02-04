# core/utils.py
import logging
from django.core.mail import send_mail
import msal
from django.conf import settings
from core.models import UserToken
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def send_recurrent_email():
    send_mail(
        'Subject here',
        'Here is the message.',
        'samaanaiapps@gmail.com',  # From email
        ['samaanai2000@gmail.com'],  # To email list
        fail_silently=False,
    )

def refresh_microsoft_token(user_token):
    """
    Refreshes the Microsoft access token using the refresh token.
    Updates the UserToken model with the new access token and expiry.
    Returns the new access token or None if refresh fails.
    """
    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.MICROSOFT_AUTH['CLIENT_ID'],
        client_credential=settings.MICROSOFT_AUTH['CLIENT_SECRET'],
        authority=settings.MICROSOFT_AUTH['AUTHORITY']
    )

    result = msal_app.acquire_token_by_refresh_token(
        refresh_token=user_token.refresh_token,
        scopes=settings.MICROSOFT_AUTH["SCOPE"]
    )

    if "access_token" in result:
        user_token.access_token = result["access_token"]
        user_token.expires_in = result.get("expires_in")
        user_token.token_type = result.get("token_type")
        if "refresh_token" in result:
            user_token.refresh_token = result["refresh_token"]
        user_token.set_token_expiry()
        user_token.save()
        logger.info(f"Refreshed Microsoft token for user: {user_token.user.username}")
        return result["access_token"]
    else:
        logger.error(f"Failed to refresh Microsoft token for user {user_token.user.username}: {result.get('error_description')}")
        return None

def is_token_expired(user_token):
    """
    Checks if the access token is expired.
    Returns True if expired, False otherwise.
    """
    if user_token.token_expires_at:
        return timezone.now() >= user_token.token_expires_at
    return False  # If no expiry info, assume not expired (adjust as needed)