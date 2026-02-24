from rest_framework import serializers

class CreditWalletSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    idempotency_key = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )

class TransferSerializer(serializers.Serializer):
    to = serializers.CharField()
    amount = serializers.IntegerField(min_value=1)
    pin = serializers.CharField(min_length=4, max_length=6)
    idempotency_key = serializers.CharField()

from rest_framework import serializers
from .models import Transaction

class TransactionHistorySerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()
    wallet_id = serializers.CharField(source="wallet.wallet_id", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True, format="%Y-%m-%d %H:%M:%S")

    # Optional: show counterparty for transfers
    counterparty_email = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ["reference", "type", "amount", "wallet_id", "timestamp", "counterparty_email"]

    def get_amount(self, obj):
        # Convert paise → rupees with 2 decimal points
        return f"{obj.amount / 100:.2f}"
    
    def get_reference(self, obj):
        return f"REF-{str(obj.reference_id).split('-')[0].upper()}"

    def get_counterparty_email(self, obj):
    # Return counterparty for any transaction that has one
        if obj.counterparty:
            return obj.counterparty.user.email
        return None


