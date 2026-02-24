import random
import string

def generate_wallet_id():
    return "WLT-" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )


# utils.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Let DRF handle known exceptions first
    response = exception_handler(exc, context)

    if response is None:
        # Fallback for unhandled exceptions
        return Response(
            {"detail": "An unexpected error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return response