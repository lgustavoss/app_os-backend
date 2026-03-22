from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock


class ConsultarCNPJEndpointTest(TestCase):
    """Testes para o endpoint de consulta de CNPJ"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.usuario)
    
    @patch('clientes.services.requests.get')
    def test_consultar_cnpj_endpoint_sucesso(self, mock_get):
        """Testa endpoint de consulta CNPJ com sucesso"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'cnpj': '12.345.678/0001-90',
            'nome': 'Empresa Teste Ltda',
            'fantasia': 'Teste',
            'email': 'contato@empresa.com.br',
            'telefone': '(11) 1234-5678',
            'logradouro': 'Rua Teste',
            'numero': '123',
            'cep': '01234-567',
            'municipio': 'São Paulo',
            'uf': 'SP'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        response = self.client.get('/api/v1/clientes/consultar_cnpj/?cnpj=12345678000190')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cnpj_cpf'], '12345678000190')
        self.assertEqual(response.data['razao_social'], 'Empresa Teste Ltda')
        self.assertEqual(response.data['email'], 'contato@empresa.com.br')
    
    def test_consultar_cnpj_sem_parametro(self):
        """Testa endpoint sem parâmetro CNPJ"""
        response = self.client.get('/api/v1/clientes/consultar_cnpj/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('erro', response.data)
    
    def test_consultar_cnpj_invalido(self):
        """Testa endpoint com CNPJ inválido (menos de 14 dígitos)"""
        response = self.client.get('/api/v1/clientes/consultar_cnpj/?cnpj=123456')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('14 dígitos', response.data['erro'])
    
    def test_consultar_cnpj_com_formatacao(self):
        """Testa que endpoint aceita CNPJ formatado"""
        with patch('clientes.services.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'cnpj': '12.345.678/0001-90',
                'nome': 'Empresa Teste',
                'fantasia': '',
                'telefone': '',
                'logradouro': '',
                'numero': '',
                'cep': '',
                'municipio': '',
                'uf': ''
            }
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            response = self.client.get('/api/v1/clientes/consultar_cnpj/?cnpj=12.345.678/0001-90')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @patch('clientes.services.requests.get')
    def test_consultar_cnpj_erro_api(self, mock_get):
        """Testa tratamento de erro da API no endpoint"""
        mock_get.side_effect = Exception('Erro de conexão')
        
        response = self.client.get('/api/v1/clientes/consultar_cnpj/?cnpj=12345678000190')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('erro', response.data)

