from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, UserProfileView, LoginView

urlpatterns = [
    # Rota para registro de novo usuário
    path('register/', RegisterView.as_view(), name='register'),
    
    # Rotas para obtenção e refresh de tokens JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Rota para perfil do usuário
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('login/', LoginView.as_view(), name='login'),
]