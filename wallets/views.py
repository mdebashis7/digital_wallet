from urllib import request
from django.shortcuts import render

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from wallets.models import Wallet, Transaction, MoneyRequest
from wallets.serializers import CreditWalletSerializer, TransferSerializer

import uuid
from users.models import TransactionPin, User

from users.utils import validate_transaction_pin

class CreditWalletAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreditWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        idempotency_key = serializer.validated_data.get("idempotency_key")

        wallet = request.user.wallet

        # 🔒 Idempotency check
        if idempotency_key:
            existing_txn = Transaction.objects.filter(
                idempotency_key=idempotency_key
            ).first()
            if existing_txn:
                return Response(
                    {
                        "message": "Already processed",
                        "transaction_id": existing_txn.transaction_id,
                        "balance": f"{wallet.balance / 100:.2f}"
                    }
                )

        # 🔒 Atomic operation
        with transaction.atomic():
            wallet.balance += amount
            wallet.save(update_fields=["balance"])

            txn = Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type=Transaction.TransactionType.CREDIT,
                idempotency_key=idempotency_key
            )

        return Response(
            {
                "message": "Wallet credited successfully",
                "transaction_id": txn.transaction_id,
                "balance": f"{wallet.balance / 100:.2f}"
            },
            status=status.HTTP_201_CREATED
        )


class TransferAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        to_value = serializer.validated_data["to"]
        pin = serializer.validated_data["pin"]
        idem_key = serializer.validated_data["idempotency_key"]

        # 🔒 PIN verification
        pin_error = validate_transaction_pin(request.user, pin)
        if pin_error:
            return pin_error

        try:
            with transaction.atomic():

                # 🔁 Lock sender wallet
                sender_wallet = (
                    Wallet.objects
                    .select_for_update()
                    .get(user=request.user)
                )

                # 🔁 Idempotency check (INSIDE lock)
                existing = Transaction.objects.filter(
                    wallet=sender_wallet,
                    idempotency_key=idem_key
                ).first()

                if existing:
                    return Response({
                        "message": "Transfer already processed",
                        "transaction_id": existing.transaction_id
                    })

                # 🎯 Resolve receiver
                if "@" in to_value:
                    receiver_user = User.objects.get(email=to_value)
                    receiver_wallet = receiver_user.wallet
                else:
                    receiver_wallet = Wallet.objects.get(wallet_id=to_value)

                # 🚫 Self transfer check
                if sender_wallet.id == receiver_wallet.id:
                    return Response(
                        {"detail": "Cannot transfer money to your own wallet"},
                        status=400
                    )

                # 🔒 Lock both wallets in consistent order
                wallet_ids = sorted([sender_wallet.id, receiver_wallet.id])

                locked_wallets = (
                    Wallet.objects
                    .select_for_update()
                    .filter(id__in=wallet_ids)
                    .order_by("id")
                )

                # Reassign correctly after locking
                locked_wallets = list(locked_wallets)
                w1, w2 = locked_wallets

                if w1.id == sender_wallet.id:
                    sender_wallet = w1
                    receiver_wallet = w2
                else:
                    sender_wallet = w2
                    receiver_wallet = w1

                # 💰 Balance check (AFTER LOCK)
                if sender_wallet.balance < amount:
                    return Response(
                        {"detail": "Insufficient balance"},
                        status=400
                    )

                reference_id = uuid.uuid4()

                # 💸 Deduct sender
                sender_wallet.balance -= amount
                sender_wallet.save(update_fields=["balance"])

                Transaction.objects.create(
                    wallet=sender_wallet,
                    amount=amount,
                    type=Transaction.TransactionType.DEBIT,
                    reference_id=reference_id,
                    idempotency_key=idem_key,
                    counterparty=receiver_wallet
                )

                # 💰 Credit receiver
                receiver_wallet.balance += amount
                receiver_wallet.save(update_fields=["balance"])

                Transaction.objects.create(
                    wallet=receiver_wallet,
                    amount=amount,
                    type=Transaction.TransactionType.CREDIT,
                    reference_id=reference_id,
                    idempotency_key=idem_key,
                    counterparty=sender_wallet
                )
                

        except (User.DoesNotExist, Wallet.DoesNotExist):
            return Response({"detail": "Recipient not found"}, status=404)

        return Response(
            {
                "message": "Transfer successful",
                "reference_id": str(reference_id)
            },
            status=status.HTTP_201_CREATED
        )


class CreateMoneyRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        to_value = request.data.get("to")
        amount = request.data.get("amount")

        if not to_value or not amount:
            return Response({"detail": "to and amount required"}, status=400)

        sender_wallet = request.user.wallet

        try:
            if "@" in to_value:
                receiver_user = User.objects.get(email=to_value)
                receiver_wallet = receiver_user.wallet
            else:
                receiver_wallet = Wallet.objects.get(wallet_id=to_value)
        except (User.DoesNotExist, Wallet.DoesNotExist):
            return Response({"detail": "Recipient not found"}, status=404)

        # 🔒 self-request guard
        if sender_wallet.id == receiver_wallet.id:
            return Response(
                {"detail": "Cannot request money from yourself"},
                status=400
            )

        req = MoneyRequest.objects.create(
            from_wallet=sender_wallet,
            to_wallet=receiver_wallet,
            amount=amount
        )

        return Response(
            {
                "message": "Money request created",
                "request_id": req.request_id
            },
            status=201
        )

class ListMoneyRequestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = request.user.wallet

        incoming = MoneyRequest.objects.filter(
            to_wallet=wallet, status="PENDING"
        )
        outgoing = MoneyRequest.objects.filter(
            from_wallet=wallet, status="PENDING"
        )

        data = {
            "incoming": [
                {
                    "request_id": r.request_id,
                    "from": r.from_wallet.wallet_id,
                    "amount": r.amount / 100,
                }
                for r in incoming
            ],
            "outgoing": [
                {
                    "request_id": r.request_id,
                    "to": r.to_wallet.wallet_id,
                    "amount": r.amount / 100,
                }
                for r in outgoing
            ],
        }

        return Response(data)

from django.db import transaction
from django.utils import timezone

class RespondMoneyRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        action = request.data.get("action")
        pin = request.data.get("pin")

        if action not in ["ACCEPT", "REJECT"]:
            return Response({"detail": "Invalid action"}, status=400)

        receiver_wallet = request.user.wallet

        # ---------------- REJECT ----------------
        if action == "REJECT":
            try:
                req = MoneyRequest.objects.get(
                    request_id=request_id,
                    status="PENDING",
                    to_wallet=receiver_wallet
                )
            except MoneyRequest.DoesNotExist:
                return Response({"detail": "Invalid request"}, status=404)

            req.status = "REJECTED"
            req.responded_at = timezone.now()
            req.save()
            return Response({"message": "Request rejected"})

        # ---------------- ACCEPT ----------------
        pin_error = validate_transaction_pin(request.user, pin)
        if pin_error:
            return pin_error

        with transaction.atomic():

            # Lock the request row first
            try:
                req = MoneyRequest.objects.select_for_update().get(
                    request_id=request_id,
                    status="PENDING",
                    to_wallet=receiver_wallet
                )
            except MoneyRequest.DoesNotExist:
                return Response({"detail": "Invalid request"}, status=404)

            sender_wallet = req.from_wallet

            # ---- Consistent wallet locking order ----
            wallets = sorted(
                [receiver_wallet, sender_wallet],
                key=lambda w: w.id
            )

            locked_wallets = (
                Wallet.objects.select_for_update()
                .filter(id__in=[w.id for w in wallets])
            )

            locked_wallets_dict = {w.id: w for w in locked_wallets}

            receiver_wallet = locked_wallets_dict[receiver_wallet.id]
            sender_wallet = locked_wallets_dict[sender_wallet.id]

            # ---- Balance check AFTER locking ----
            if receiver_wallet.balance < req.amount:
                return Response({"detail": "Insufficient balance"}, status=400)

            # ---- Update balances ----
            receiver_wallet.balance -= req.amount
            sender_wallet.balance += req.amount

            receiver_wallet.save()
            sender_wallet.save()
            idem_key = f"money-request-{req.request_id}"
            # ---- Create transactions ----
            reference_id = uuid.uuid4()

            Transaction.objects.create(
                wallet=receiver_wallet,
                amount=req.amount,
                type="DEBIT",
                reference_id=reference_id,
                idempotency_key=idem_key,
                counterparty=sender_wallet
            )
            
            

            Transaction.objects.create(
                wallet=sender_wallet,
                amount=req.amount,
                type="CREDIT",
                reference_id=reference_id,
                idempotency_key=idem_key,
                counterparty=receiver_wallet
            )

            # ---- Update request status ----
            req.status = "ACCEPTED"
            req.responded_at = timezone.now()
            req.save()

        return Response({"message": "Request accepted"})
    
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionHistorySerializer

class TransactionHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = request.user.wallet
        transactions = wallet.transactions.all().order_by("-created_at")
        serializer = TransactionHistorySerializer(transactions, many=True)
        return Response(serializer.data)

