from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'login-view-tests',
        }
    },
    LOGIN_RATE_LIMIT='1000/m',
)
class LoginViewTest(TestCase):
    """Testes para o endpoint de login"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_login_sucesso(self):
        """Testa login com credenciais válidas"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/v1/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('mensagem', response.data)
        self.assertIn('usuario', response.data)
        self.assertEqual(response.data['usuario']['email'], 'test@example.com')
        # Verificar que a sessão foi criada
        self.assertIn('_auth_user_id', self.client.session)
    
    def test_login_credenciais_invalidas(self):
        """Testa login com credenciais inválidas"""
        data = {
            'email': 'test@example.com',
            'password': 'senha_errada'
        }
        
        response = self.client.post('/api/v1/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('erro', response.data)
    
    def test_login_usuario_inexistente(self):
        """Testa login com usuário que não existe"""
        data = {
            'email': 'naoexiste@example.com',
            'password': 'senha123'
        }
        
        response = self.client.post('/api/v1/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('erro', response.data)
    
    def test_login_dados_invalidos(self):
        """Testa login sem fornecer dados obrigatórios"""
        data = {
            'email': 'test@example.com'
            # password faltando
        }
        
        response = self.client.post('/api/v1/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_usuario_inativo(self):
        """Testa login com usuário inativo"""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/v1/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('erro', response.data)


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'login-ratelimit-tests',
        }
    },
    LOGIN_RATE_LIMIT='3/m',
)
class LoginRatelimitTest(TestCase):
    """Após o limite, o endpoint de login responde 429."""

    def setUp(self):
        self.client = APIClient()
        User.objects.create_user(
            username='limuser',
            password='limpass123',
            email='lim@example.com',
        )

    def test_login_bloqueado_apos_varias_tentativas(self):
        data = {'email': 'lim@example.com', 'password': 'errada'}
        for _ in range(3):
            self.client.post('/api/v1/auth/login/', data, format='json')
        r4 = self.client.post('/api/v1/auth/login/', data, format='json')
        self.assertEqual(r4.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('erro', r4.data)


class LogoutViewTest(TestCase):
    """Testes para o endpoint de logout"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Fazer login primeiro
        self.client.force_authenticate(user=self.user)
    
    def test_logout_sucesso(self):
        """Testa logout com usuário autenticado"""
        response = self.client.post('/api/v1/auth/logout/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('mensagem', response.data)
    
    def test_logout_sem_autenticacao(self):
        """Testa logout sem estar autenticado"""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/v1/auth/logout/')
        
        # IsAuthenticated retorna 403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserViewTest(TestCase):
    """Testes para o endpoint de usuário atual"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_obter_usuario_autenticado(self):
        """Testa obtenção de informações do usuário autenticado"""
        response = self.client.get('/api/v1/auth/user/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertIn('id', response.data)
        self.assertIn('date_joined', response.data)
    
    def test_obter_usuario_sem_autenticacao(self):
        """Testa obtenção de usuário sem estar autenticado"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/auth/user/')
        
        # IsAuthenticated retorna 403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CsrfCookieViewTest(TestCase):
    """GET /api/v1/auth/csrf/ — token no JSON e cookie para front noutra origem."""

    def test_retorna_csrf_e_cookie(self):
        client = APIClient()
        response = client.get('/api/v1/auth/csrf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrfToken', response.data)
        self.assertGreater(len(response.data['csrfToken']), 10)
        self.assertIn('csrftoken', client.cookies)

