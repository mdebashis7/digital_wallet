from django.contrib import admin
from .models import Wallet

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("wallet_id", "user", "balance", "created_at")
    search_fields = ("wallet_id", "user__email")
