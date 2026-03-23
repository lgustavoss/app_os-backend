from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.core import is_ratelimited
from rest_framework import status, views, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from configuracoes.models import ConfiguracaoEmpresa
from .models import PerfilUsuario
from .serializers import (
    LoginSerializer,
    UserSerializer,
    UsuarioSistemaSerializer,
    ValidarSenhaEntradaSerializer,
    checar_regras_senha,
)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfCookieView(views.APIView):
    """
    GET — devolve o token CSRF no JSON e define o cookie csrftoken no domínio da API.

    Com front e API em origens diferentes, o JavaScript do SPA não lê cookies da API
    via document.cookie; o cliente deve chamar este endpoint e enviar o token em
    X-CSRFToken nos métodos não seguros (sessão + DRF).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({'csrfToken': get_token(request)})


class LoginView(views.APIView):
    """
    Endpoint para autenticação de usuários.
    
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Realiza login do usuário"""
        if is_ratelimited(
            request._request,
            group='auth_login',
            key='ip',
            rate=getattr(settings, 'LOGIN_RATE_LIMIT', '20/m'),
            method='POST',
            increment=True,
        ):
            return Response(
                {
                    'erro': 'Muitas tentativas de login. Aguarde e tente novamente.',
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email'].strip().lower()
        password = serializer.validated_data['password']

        UserModel = get_user_model()
        try:
            user_obj = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            user_obj = None

        user = (
            authenticate(request, username=user_obj.username, password=password)
            if user_obj
            else None
        )

        if user is None:
            return Response(
                {'erro': 'Credenciais inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'erro': 'Usuário inativo'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        login(request, user)
        get_empresa_atual(request)  # garante perfil e empresa atual
        user_refreshed = get_user_model().objects.select_related(
            'perfil', 'perfil__empresa_atual'
        ).get(pk=user.pk)
        user_serializer = UserSerializer(user_refreshed)
        return Response({
            'mensagem': 'Login realizado com sucesso',
            'usuario': user_serializer.data
        }, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    """
    Endpoint para logout de usuários.
    
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Realiza logout do usuário"""
        logout(request)
        return Response(
            {'mensagem': 'Logout realizado com sucesso'},
            status=status.HTTP_200_OK
        )


def get_empresa_atual(request):
    """
    Retorna a empresa atual do usuário (do perfil). Se não houver perfil ou
    empresa definida, cria/atualiza o perfil com a primeira empresa.
    Sempre lê o perfil na BD (evita cache do OneToOne no mesmo objeto User — ex.: test client).
    """
    perfil = (
        PerfilUsuario.objects.filter(user_id=request.user.pk)
        .select_related('empresa_atual')
        .first()
    )
    if perfil is None:
        perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
    if perfil.empresa_atual_id:
        return perfil.empresa_atual
    primeira = ConfiguracaoEmpresa.objects.order_by('id').first()
    if primeira:
        perfil.empresa_atual = primeira
        perfil.save(update_fields=['empresa_atual'])
    return primeira


class ValidarSenhaView(views.APIView):
    """
    Pré-valida a senha com as mesmas regras do Django (AUTH_PASSWORD_VALIDATORS).
    Usado pelo formulário de usuários ao sair do campo senha.

    POST /api/auth/validar-senha/
    Body: { "password": "...", "usuario_id": 12 }  (usuario_id opcional, para edição)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = ValidarSenhaEntradaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        usuario_id = serializer.validated_data.get('usuario_id')
        alvo = None
        if usuario_id is not None:
            alvo = get_object_or_404(User, pk=usuario_id)
        resultado = checar_regras_senha(password, user=alvo)
        return Response(resultado, status=status.HTTP_200_OK)


class UserView(views.APIView):
    """
    Endpoint para obter e atualizar informações do usuário autenticado.
    
    GET /api/auth/user/ - retorna usuário, empresa_atual e lista de empresas
    PATCH /api/auth/user/ - altera empresa_atual (body: { "empresa_atual": id })
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna informações do usuário autenticado (com perfil e empresa atual)."""
        user = get_user_model().objects.select_related(
            'perfil', 'perfil__empresa_atual'
        ).get(pk=request.user.pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Altera a empresa atual do usuário"""
        empresa_id = request.data.get('empresa_atual')
        if empresa_id is None:
            return Response(
                {'erro': 'Campo empresa_atual é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            empresa = ConfiguracaoEmpresa.objects.get(pk=empresa_id)
        except ConfiguracaoEmpresa.DoesNotExist:
            return Response(
                {'erro': 'Empresa não encontrada'},
                status=status.HTTP_404_NOT_FOUND,
            )
        perfil, _ = PerfilUsuario.objects.get_or_create(
            user=request.user,
            defaults={'empresa_atual': empresa},
        )
        perfil.empresa_atual = empresa
        perfil.save(update_fields=['empresa_atual'])
        user_refreshed = get_user_model().objects.select_related(
            'perfil', 'perfil__empresa_atual'
        ).get(pk=request.user.pk)
        serializer = UserSerializer(user_refreshed)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuários do sistema (apenas staff / administrador).
    Desativar usuário: DELETE (define is_active=False).
    """
    queryset = User.objects.all().order_by('email')
    serializer_class = UsuarioSistemaSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pk == request.user.pk:
            return Response(
                {'erro': 'Não é possível desativar o próprio usuário.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)
