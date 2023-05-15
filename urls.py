from django.urls import include, path

from modules.urls import url
from users import views


user_view = views.UserViewset.as_view(
    {
        'post': 'create',
    }
)

from rest_framework_social_oauth2.views import (
    ConvertTokenView,
    RevokeTokenView,
    # FacebookLogin,
    # GoogleLogin,
)

urlpatterns = [
    path('', user_view),
    path('sync-from-website', views.SyncUsers.as_view()),
    path("auth/", include('rest_framework_social_oauth2.urls')),
    path("auth/forgot-password/", views.ForgotPasswordView.as_view()),
    path("auth/verify-token/", views.VerifyTokenView.as_view()),
    path("api/verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
]
