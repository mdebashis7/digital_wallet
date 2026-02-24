from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import authenticate,login, logout

from users.models import User
from users.serializers import SignupSerializer
from users.serializers import SetPinSerializer
from users.serializers import LoginSerializer
from users.serializers import WalletBalanceSerializer

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User created successfully",
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SetPinAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SetPinSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Transaction PIN set successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)  # sets Django session
            return Response({"message": "Login successful"}, status=200)
        return Response(serializer.errors, status=400)

class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)  # removes session
        return Response({"message": "Logout successful"}, status=200)

class CheckBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = request.user.wallet  
        serializer = WalletBalanceSerializer(wallet)
        return Response(serializer.data)


from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from wallets.models import Wallet  # <-- this is your wallets/models.py Wallet class

User = get_user_model()

class SearchUsersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response([])

        results = []
        # search by email
        users_by_email = User.objects.filter(email__icontains=q).exclude(id=request.user.id).select_related("wallet")
        for u in users_by_email:
            results.append({
                "email": u.email,
                "wallet_id": u.wallet.wallet_id if hasattr(u, "wallet") else None
            })

        # search by wallet_id
        wallets_by_id = Wallet.objects.filter(wallet_id__icontains=q).exclude(user=request.user).select_related("user")
        for w in wallets_by_id:
            results.append({
                "email": w.user.email,
                "wallet_id": w.wallet_id
            })

        # deduplicate if someone matches both
        seen = set()
        final_results = []
        for r in results:
            if r["wallet_id"] not in seen:
                seen.add(r["wallet_id"])
                final_results.append(r)

        return Response(final_results)
