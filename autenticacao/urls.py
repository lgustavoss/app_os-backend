from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LoginView, LogoutView, UserView, UsuarioViewSet, ValidarSenhaView

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/user/', UserView.as_view(), name='user'),
    path('auth/validar-senha/', ValidarSenhaView.as_view(), name='validar-senha'),
] + router.urls

