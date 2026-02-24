from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from wallets.models import Wallet
from wallets.utils import generate_wallet_id

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet_for_user(sender, instance, created, **kwargs):
    if not created:
        return

    wallet_id = generate_wallet_id()

    Wallet.objects.create(
        user=instance,
        wallet_id=wallet_id
    )
