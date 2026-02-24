from rest_framework import serializers
from users.models import User
from users.models import TransactionPin



class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)  # hashes password
        user.save()
        return user
    
class SetPinSerializer(serializers.Serializer):
    pin = serializers.CharField(write_only=True, min_length=4)

    def validate_pin(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("PIN must contain only digits")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user

        tx_pin, _ = TransactionPin.objects.get_or_create(user=user)
        tx_pin.set_pin(self.validated_data["pin"])
        tx_pin.save()

        return tx_pin



from django.contrib.auth import authenticate

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        attrs['user'] = user
        return attrs


from wallets.models import Wallet

class WalletBalanceSerializer(serializers.ModelSerializer):
    walletId = serializers.CharField(source="wallet_id")
    balance = serializers.SerializerMethodField() 
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    has_pin = serializers.SerializerMethodField()
    class Meta:
        model = Wallet
        fields = ["walletId", "balance","first_name","email","has_pin"]

    def get_balance(self, obj):
        # convert paise to rupees with 2 decimal points
        return f"{obj.balance/100:.2f}"
    def get_has_pin(self, obj):
        return hasattr(obj.user, "transaction_pin")

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSearchSerializer(serializers.ModelSerializer):
    wallet_id = serializers.CharField(source="wallet.wallet_id")  # include wallet ID

    class Meta:
        model = User
        fields = ["email", "wallet_id", "first_name", "last_name"]
       