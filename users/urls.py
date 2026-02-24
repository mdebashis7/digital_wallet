from django.urls import path
from users.views import SignupAPIView, SetPinAPIView, LoginAPIView, LogoutAPIView, CheckBalanceAPIView, SearchUsersAPIView


urlpatterns = [
    path("signup/", SignupAPIView.as_view(), name="signup"),
    path("set-pin/", SetPinAPIView.as_view(), name="set-pin"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("balance/", CheckBalanceAPIView.as_view(), name="check-balance"),
    path("search-users/", SearchUsersAPIView.as_view(), name="search-users"),
]


