from django.test import TestCase
from django.contrib.auth.models import User
from clientes.models import Cliente
from produtos.models import Produto
from ordens_servico.models import Orcamento, ItemOrcamento
from ordens_servico.tests.support import criar_empresa, criar_status
from ordens_servico.serializers import (
    OrcamentoSerializer,
    OrcamentoCreateSerializer,
    ItemOrcamentoSerializer,
)


class OrcamentoSerializerTest(TestCase):
    """Testes para os serializers de Orçamento"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.usuario = User.objects.create_user(
            username='vendedor',
            password='testpass123'
        )
        self.empresa = criar_empresa(cnpj='66777888000181', razao_social='Empresa Serializer')
        self.cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste Ltda',
            usuario_cadastro=self.usuario
        )
        self.st = criar_status('Rascunho', ordem=1)
        self.orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Serviços de manutenção',
            status=self.st,
            usuario_criacao=self.usuario
        )
    
    def test_ordem_servico_serializer(self):
        """Testa o OrcamentoSerializer"""
        serializer = OrcamentoSerializer(self.orcamento)
        data = serializer.data
        
        self.assertIn('numero', data)
        self.assertTrue(data['numero'].startswith('ORC-'))
        self.assertEqual(data['cliente'], self.cliente.id)
        self.assertEqual(data['cliente_nome'], 'Empresa Teste Ltda')
        self.assertIn('data_criacao', data)
        self.assertIn('itens', data)
    
    def test_ordem_servico_create_serializer_valid(self):
        """Testa criação de orçamento com serializer válido (sem número)"""
        data = {
            'cliente': self.cliente.id,
            'descricao': 'Novo orçamento',
            'status': self.st.id,
        }

        serializer = OrcamentoCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Verificar que número será gerado automaticamente
        orcamento = serializer.save(usuario_criacao=self.usuario, empresa=self.empresa)
        self.assertTrue(orcamento.numero.startswith('ORC-'))
    
    def test_ordem_servico_create_serializer_com_itens(self):
        """Testa criação de orçamento com itens no payload"""
        data = {
            'cliente': self.cliente.id,
            'descricao': 'Orçamento com itens',
            'status': self.st.id,
            'itens': [
                {
                    'tipo': 'servico',
                    'descricao': 'Mão de obra',
                    'quantidade': 2,
                    'valor_unitario': '250.00'
                }
            ]
        }
        
        serializer = OrcamentoCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Criar o orçamento
        orcamento = serializer.save(usuario_criacao=self.usuario, empresa=self.empresa)
        
        # Verificar que o orçamento foi criado com número gerado automaticamente
        self.assertTrue(orcamento.numero.startswith('ORC-'))
        
        # Verificar que os itens foram criados
        self.assertEqual(orcamento.itens.count(), 1)
        item = orcamento.itens.first()
        self.assertEqual(item.descricao, 'Mão de obra')
        self.assertEqual(item.tipo, 'servico')
        
        # Verificar que valor total foi calculado
        self.assertEqual(float(orcamento.valor_total), 500.00)
    
    def test_ordem_servico_create_serializer_invalid(self):
        """Testa criação de orçamento com dados inválidos"""
        data = {
            'numero': 'ORC-002',
            # cliente faltando
            'descricao': 'Teste'
        }
        
        serializer = OrcamentoCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_create_serializer_sem_status_invalido(self):
        data = {'cliente': self.cliente.id, 'descricao': 'X'}
        serializer = OrcamentoCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)


class ItemOrcamentoSerializerTest(TestCase):
    """Testes para os serializers de Item de Orçamento"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.usuario = User.objects.create_user(
            username='vendedor',
            password='testpass123'
        )
        self.empresa = criar_empresa(cnpj='77888999000181', razao_social='Empresa Item Ser')
        self.cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste',
            usuario_cadastro=self.usuario
        )
        self.st_item = criar_status('Item', ordem=1)
        self.orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_item,
            usuario_criacao=self.usuario
        )
    
    def test_item_servico_serializer(self):
        """Testa o ItemOrcamentoSerializer"""
        item = ItemOrcamento.objects.create(
            orcamento=self.orcamento,
            tipo='servico',
            descricao='Mão de obra',
            quantidade=2,
            valor_unitario=250.00
        )
        
        serializer = ItemOrcamentoSerializer(item)
        data = serializer.data
        
        self.assertEqual(data['descricao'], 'Mão de obra')
        self.assertEqual(data['tipo'], 'servico')
        self.assertEqual(data['quantidade'], 2)
        self.assertEqual(float(data['valor_unitario']), 250.00)
        self.assertEqual(float(data['valor_total']), 500.00)
    
    def test_item_servico_create_serializer_valid(self):
        """Testa criação de item com serializer válido"""
        Produto.objects.create(codigo=1, descricao='Peça X', valor=100)
        data = {
            'orcamento': self.orcamento.id,
            'tipo': 'peca',
            'produto': 1,
            'descricao': 'Peça X',
            'quantidade': 1,
            'valor_unitario': '100.00'
        }
        
        serializer = ItemOrcamentoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_item_servico_create_serializer_invalid(self):
        """Testa criação de item com dados inválidos"""
        data = {
            'tipo': 'servico',
            'descricao': 'Teste'
            # quantidade e valor_unitario faltando
        }
        
        serializer = ItemOrcamentoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
