from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from clientes.models import Cliente


class ClienteViewSetTest(TestCase):
    """Testes para o ViewSet de Clientes"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.usuario)
        
        # Criar alguns clientes de teste
        self.cliente1 = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste 1 Ltda',
            nome_fantasia='Teste 1',
            usuario_cadastro=self.usuario
        )
        self.cliente2 = Cliente.objects.create(
            cnpj_cpf='98765432000110',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste 2 Ltda',
            nome_fantasia='Teste 2',
            usuario_cadastro=self.usuario
        )
    
    def test_listar_clientes(self):
        """Testa listagem de clientes"""
        response = self.client.get('/api/v1/clientes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_listar_clientes_requer_autenticacao(self):
        """Testa que listagem requer autenticação"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/clientes/')
        
        # IsAuthenticated retorna 403, não 401
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_obter_detalhes_cliente(self):
        """Testa obtenção de detalhes de um cliente"""
        response = self.client.get(f'/api/v1/clientes/{self.cliente1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cnpj_cpf'], '12345678000190')
        self.assertEqual(response.data['razao_social'], 'Empresa Teste 1 Ltda')
    
    def test_criar_cliente(self):
        """Testa criação de novo cliente"""
        data = {
            'cnpj_cpf': '11111111000111',
            'tipo_documento': 'CNPJ',
            'razao_social': 'Nova Empresa Ltda',
            'nome_fantasia': 'Nova Empresa',
            'telefone': '(11) 9876-5432',
            'endereco': 'Rua Nova, 456',
            'cep': '12345678',
            'cidade': 'Rio de Janeiro',
            'estado': 'RJ'
        }
        
        response = self.client.post('/api/v1/clientes/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['razao_social'], 'Nova Empresa Ltda')
        # Verificar que retorna dados completos após criação
        self.assertIn('usuario_cadastro', response.data)
        self.assertIn('data_cadastro', response.data)
    
    def test_criar_cliente_cnpj_duplicado(self):
        """Testa que não permite criar cliente com CNPJ duplicado"""
        data = {
            'cnpj_cpf': '12345678000190',  # Já existe
            'tipo_documento': 'CNPJ',
            'razao_social': 'Outra Empresa'
        }
        
        response = self.client.post('/api/v1/clientes/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_atualizar_cliente(self):
        """Testa atualização de cliente"""
        data = {
            'telefone': '(11) 9999-8888'
        }
        
        response = self.client.patch(
            f'/api/v1/clientes/{self.cliente1.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['telefone'], '(11) 9999-8888')
        self.assertEqual(response.data['usuario_ultima_alteracao'], self.usuario.id)
        
        # Verificar no banco
        self.cliente1.refresh_from_db()
        self.assertEqual(self.cliente1.telefone, '(11) 9999-8888')
    
    def test_deletar_cliente(self):
        """Testa soft delete de cliente (marca como inativo)"""
        response = self.client.delete(f'/api/v1/clientes/{self.cliente1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('mensagem', response.data)
        
        # Verificar que o cliente ainda existe mas está inativo
        cliente = Cliente.objects.get(id=self.cliente1.id)
        self.assertFalse(cliente.ativo)
        self.assertEqual(cliente.usuario_ultima_alteracao, self.usuario)
    
    def test_listar_apenas_clientes_ativos(self):
        """Testa que apenas clientes ativos são listados por padrão"""
        # Criar um cliente inativo
        cliente_inativo = Cliente.objects.create(
            cnpj_cpf='99999999000199',
            tipo_documento='CNPJ',
            razao_social='Cliente Inativo',
            usuario_cadastro=self.usuario,
            ativo=False
        )
        
        response = self.client.get('/api/v1/clientes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que apenas clientes ativos aparecem
        ids = [c['id'] for c in response.data['results']]
        self.assertIn(self.cliente1.id, ids)
        self.assertIn(self.cliente2.id, ids)
        self.assertNotIn(cliente_inativo.id, ids)
    
    def test_listar_incluindo_inativos(self):
        """Testa que é possível listar clientes inativos com parâmetro"""
        # Criar um cliente inativo
        cliente_inativo = Cliente.objects.create(
            cnpj_cpf='99999999000199',
            tipo_documento='CNPJ',
            razao_social='Cliente Inativo',
            usuario_cadastro=self.usuario,
            ativo=False
        )
        
        response = self.client.get('/api/v1/clientes/?incluir_inativos=true')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que todos os clientes aparecem
        ids = [c['id'] for c in response.data['results']]
        self.assertIn(self.cliente1.id, ids)
        self.assertIn(self.cliente2.id, ids)
        self.assertIn(cliente_inativo.id, ids)
    
    def test_filtrar_por_cnpj_cpf(self):
        """Testa filtro por CNPJ/CPF"""
        response = self.client.get('/api/v1/clientes/?cnpj_cpf=12345678')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['cnpj_cpf'], '12345678000190')
    
    def test_filtrar_por_razao_social(self):
        """Testa filtro por razão social"""
        response = self.client.get('/api/v1/clientes/?razao_social=Teste 2')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['razao_social'], 'Empresa Teste 2 Ltda')

