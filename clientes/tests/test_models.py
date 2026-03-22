from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from clientes.models import Cliente


class ClienteModelTest(TestCase):
    """Testes para o modelo Cliente"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.usuario = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_criar_cliente_cnpj(self):
        """Testa criação de cliente com CNPJ"""
        cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste Ltda',
            nome_fantasia='Teste',
            telefone='(11) 1234-5678',
            endereco='Rua Teste, 123',
            cep='01234567',
            cidade='São Paulo',
            estado='SP',
            usuario_cadastro=self.usuario
        )
        
        self.assertEqual(cliente.cnpj_cpf, '12345678000190')
        self.assertEqual(cliente.tipo_documento, 'CNPJ')
        self.assertEqual(cliente.razao_social, 'Empresa Teste Ltda')
        self.assertIsNotNone(cliente.data_cadastro)
        self.assertEqual(cliente.usuario_cadastro, self.usuario)
    
    def test_criar_cliente_cpf(self):
        """Testa criação de cliente com CPF"""
        cliente = Cliente.objects.create(
            cnpj_cpf='12345678901',
            tipo_documento='CPF',
            razao_social='João Silva',
            usuario_cadastro=self.usuario
        )
        
        self.assertEqual(cliente.tipo_documento, 'CPF')
        self.assertEqual(cliente.razao_social, 'João Silva')
    
    def test_cnpj_cpf_unico(self):
        """Testa que CNPJ/CPF deve ser único"""
        Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa 1',
            usuario_cadastro=self.usuario
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            Cliente.objects.create(
                cnpj_cpf='12345678000190',
                tipo_documento='CNPJ',
                razao_social='Empresa 2',
                usuario_cadastro=self.usuario
            )
    
    def test_str_representation(self):
        """Testa a representação em string do modelo"""
        cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste Ltda',
            usuario_cadastro=self.usuario
        )
        
        expected = 'Empresa Teste Ltda - 12345678000190'
        self.assertEqual(str(cliente), expected)
    
    def test_ordenacao_por_razao_social(self):
        """Testa que clientes são ordenados por razão social"""
        Cliente.objects.create(
            cnpj_cpf='11111111000111',
            tipo_documento='CNPJ',
            razao_social='Zebra Ltda',
            usuario_cadastro=self.usuario
        )
        Cliente.objects.create(
            cnpj_cpf='22222222000222',
            tipo_documento='CNPJ',
            razao_social='Alpha Ltda',
            usuario_cadastro=self.usuario
        )
        
        clientes = Cliente.objects.all()
        self.assertEqual(clientes[0].razao_social, 'Alpha Ltda')
        self.assertEqual(clientes[1].razao_social, 'Zebra Ltda')
    
    def test_campos_opcionais(self):
        """Testa que campos opcionais podem ser nulos"""
        cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste',
            usuario_cadastro=self.usuario
        )
        
        self.assertIsNone(cliente.nome_fantasia)
        self.assertIsNone(cliente.telefone)
        self.assertIsNone(cliente.endereco)
        self.assertIsNone(cliente.usuario_ultima_alteracao)

