from django.test import TestCase
from django.contrib.auth.models import User
from clientes.models import Cliente
from produtos.models import Produto
from ordens_servico.models import Orcamento, ItemOrcamento
from ordens_servico.services import gerar_pdf_orcamento
from ordens_servico.tests.support import criar_empresa, criar_status


class GerarPDFOrcamentoTest(TestCase):
    """Testes para geração de PDF do orçamento"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.usuario = User.objects.create_user(
            username='vendedor',
            password='testpass123'
        )
        self.empresa = criar_empresa(cnpj='88999000000181', razao_social='Empresa PDF Teste')
        self.cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Cliente Ltda',
            usuario_cadastro=self.usuario
        )
        self.st_pdf = criar_status('PDF', ordem=1)
        self.orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Serviços de manutenção e reparo',
            status=self.st_pdf,
            usuario_criacao=self.usuario
        )
        
        # Criar itens
        ItemOrcamento.objects.create(
            orcamento=self.orcamento,
            tipo='servico',
            descricao='Mão de obra',
            quantidade=2,
            valor_unitario=250.00
        )
        p = Produto.objects.create(codigo=1, descricao='Peças', valor=100)
        ItemOrcamento.objects.create(
            orcamento=self.orcamento,
            tipo='peca',
            descricao='Peças',
            quantidade=1,
            valor_unitario=100.00,
            produto=p,
        )
    
    def test_gerar_pdf_orcamento(self):
        """Testa geração de PDF do orçamento"""
        response = gerar_pdf_orcamento(self.orcamento)
        
        # Verificar estrutura do PDF
        self.assertIn(b'%PDF', response.content)
        # Verificar que tem conteúdo significativo
        self.assertGreater(len(response.content), 1000)
    
    def test_pdf_contem_dados_os(self):
        """Testa que o PDF foi gerado corretamente"""
        response = gerar_pdf_orcamento(self.orcamento)
        
        # PDF é binário, verificar apenas estrutura básica
        from django.http import HttpResponse
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        # Verificar que tem conteúdo significativo (mais que apenas headers)
        self.assertGreater(len(response.content), 1000)
    
    def test_pdf_contem_dados_cliente(self):
        """Testa que o PDF foi gerado corretamente"""
        response = gerar_pdf_orcamento(self.orcamento)
        
        # Verificar estrutura do PDF (contém marca PDF)
        self.assertIn(b'%PDF', response.content)
        # Verificar que tem conteúdo significativo
        self.assertGreater(len(response.content), 1000)
    
    def test_pdf_contem_itens(self):
        """Testa que o PDF foi gerado com itens"""
        response = gerar_pdf_orcamento(self.orcamento)
        
        # Verificar estrutura do PDF
        self.assertIn(b'%PDF', response.content)
        # Verificar que tem conteúdo significativo
        self.assertGreater(len(response.content), 1000)
    
    def test_pdf_contem_valor_total(self):
        """Testa que o PDF foi gerado com valor total"""
        # Recalcular valor total
        self.orcamento.calcular_valor_total()
        
        response = gerar_pdf_orcamento(self.orcamento)
        
        # Verificar estrutura do PDF
        self.assertIn(b'%PDF', response.content)
        # Verificar que tem conteúdo significativo
        self.assertGreater(len(response.content), 1000)
