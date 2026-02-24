from rest_framework.response import Response
from rest_framework import status


def validate_transaction_pin(user, raw_pin):
    try:
        tx_pin = user.transaction_pin
    except Exception:
        return Response(
            {"detail": "Transaction PIN not set"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check lock
    if tx_pin.is_locked():
        return Response(
            {"detail": "Transaction PIN locked. Try again after 10 minutes."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Validate pin
    if not raw_pin or not tx_pin.verify_pin(raw_pin):
        tx_pin.register_failure()
        remaining = max(0, 3 - tx_pin.failed_attempts)

        return Response(
            {
                "detail": "Invalid PIN",
                "remaining_attempts": remaining
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Success → reset failures
    tx_pin.reset_failures()
    return None
