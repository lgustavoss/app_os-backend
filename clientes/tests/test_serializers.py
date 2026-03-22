from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from clientes.models import Cliente
from clientes.serializers import ClienteSerializer, ClienteCreateSerializer


class ClienteSerializerTest(TestCase):
    """Testes para os serializers de Cliente"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.usuario = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_cliente_serializer(self):
        """Testa o ClienteSerializer"""
        cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste Ltda',
            nome_fantasia='Teste',
            usuario_cadastro=self.usuario
        )
        
        serializer = ClienteSerializer(cliente)
        data = serializer.data
        
        self.assertEqual(data['cnpj_cpf'], '12345678000190')
        self.assertEqual(data['tipo_documento'], 'CNPJ')
        self.assertEqual(data['razao_social'], 'Empresa Teste Ltda')
        self.assertEqual(data['usuario_cadastro_nome'], 'testuser')
        self.assertIn('data_cadastro', data)
    
    def test_cliente_create_serializer_valid(self):
        """Testa criação de cliente com serializer válido"""
        data = {
            'cnpj_cpf': '12345678000190',
            'tipo_documento': 'CNPJ',
            'razao_social': 'Empresa Teste Ltda',
            'nome_fantasia': 'Teste',
            'telefone': '(11) 1234-5678',
            'endereco': 'Rua Teste, 123',
            'cep': '01234567',
            'cidade': 'São Paulo',
            'estado': 'SP'
        }
        
        serializer = ClienteCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_cliente_create_serializer_invalid(self):
        """Testa criação de cliente com dados inválidos"""
        data = {
            'cnpj_cpf': '',  # Campo obrigatório vazio
            'tipo_documento': 'CNPJ',
            'razao_social': 'Empresa Teste'
        }
        
        serializer = ClienteCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cnpj_cpf', serializer.errors)

