# core/utils.py
import logging
from django.core.mail import send_mail
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render  # Import render

logger = logging.getLogger(__name__)

def send_email(subject, message, recipient_list):
    try:
        # --- Logging ---
        logger.info('Preparing to send email to %s ...', recipient_list)
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,  # Pass the recipient *list*
            fail_silently=False,
        )
        logger.info('Email sent successfully.')
        return HttpResponse("Email sent successfully!")

    except Exception as e:
        # --- Error Handling ---
        logger.exception("Email sending failed")  # Log full traceback + message
        return HttpResponse(f"Email sending failed: {e}", status=500)
