from django.urls import path
from wallets.views import CreditWalletAPIView, TransferAPIView, TransactionHistoryAPIView, CreateMoneyRequestAPIView, ListMoneyRequestsAPIView, RespondMoneyRequestAPIView

urlpatterns = [
    path("credit/", CreditWalletAPIView.as_view(), name="credit-wallet"),
    path("transfer/", TransferAPIView.as_view(),   name="wallet-transfer"),
    path("request/", CreateMoneyRequestAPIView.as_view()),
    path("requests/", ListMoneyRequestsAPIView.as_view()),
    path("request/<str:request_id>/respond/", RespondMoneyRequestAPIView.as_view()),
    path("transactions/", TransactionHistoryAPIView.as_view(), name="transaction-history"),

]



