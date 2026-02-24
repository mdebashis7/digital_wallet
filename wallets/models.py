import uuid
from django.db import models
from django.conf import settings

from django.db.models import Q,CheckConstraint

from django.core.validators import MinValueValidator


class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet"
    )

    wallet_id = models.CharField(max_length=15, unique=True)
    balance = models.BigIntegerField(default=0,
        validators=[MinValueValidator(0)])  # stored in paise

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            CheckConstraint(condition=Q(balance__gte=0), name="balance_non_negative")
        ]


    def __str__(self):
        return f"{self.wallet_id} - {self.user.email}"


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"
        TRANSFER = "TRANSFER", "Transfer"

    class TransactionStatus(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    transaction_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    counterparty = models.ForeignKey(
        "wallets.Wallet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="counterparty_transactions"
    )

    wallet = models.ForeignKey(
        "wallets.Wallet",
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    amount = models.BigIntegerField()  # paise, always positive

    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices
    )

    status = models.CharField(
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.SUCCESS
    )

    reference_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True
    )
    idempotency_key = models.CharField(
        max_length=100,
        blank=False,
        null=False
    )

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["wallet", "idempotency_key"],
                name="unique_wallet_idempotency"
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="amount_must_be_positive"
            )
        ]

        indexes = [
            models.Index(fields=["wallet", "-created_at"])
        ]
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)


class MoneyRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request_id = models.CharField(max_length=20, unique=True, editable=False)

    from_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="outgoing_requests"
    )

    to_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="incoming_requests"
    )

    amount = models.BigIntegerField()  # paise
    note = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = f"REQ{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
