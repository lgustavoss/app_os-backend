from django.test import TestCase
from django.contrib.auth.models import User
from clientes.models import Cliente
from ordens_servico.models import Orcamento, ItemOrcamento, StatusOrcamento
from ordens_servico.tests.support import criar_empresa, criar_status


class OrcamentoModelTest(TestCase):
    """Testes para o modelo Orcamento"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.usuario = User.objects.create_user(
            username='vendedor',
            password='testpass123',
            email='vendedor@example.com'
        )
        self.empresa = criar_empresa(cnpj='33444555000181', razao_social='Empresa Modelo Teste')
        self.cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste Ltda',
            usuario_cadastro=self.usuario
        )
        self.st_padrao = criar_status('Padrão', ordem=0)
    
    def test_criar_orcamento(self):
        """Testa criação de orçamento"""
        st = criar_status('Em aberto', ordem=1)
        orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Serviços de manutenção',
            status=st,
            usuario_criacao=self.usuario
        )

        self.assertTrue(orcamento.numero.startswith('ORC-'))
        self.assertEqual(orcamento.cliente, self.cliente)
        self.assertEqual(orcamento.descricao, 'Serviços de manutenção')
        self.assertEqual(orcamento.status_id, st.id)
        self.assertEqual(orcamento.valor_total, 0.00)
    
    def test_gerar_proximo_numero(self):
        """Testa geração de número sequencial"""
        # Primeiro número deve ser ORC-001
        numero1 = Orcamento.gerar_proximo_numero(self.empresa)
        self.assertEqual(numero1, 'ORC-001')
        
        # Criar orçamento com esse número
        Orcamento.objects.create(
            numero=numero1,
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste 1',
            status=self.st_padrao,
            usuario_criacao=self.usuario
        )
        
        # Próximo número deve ser ORC-002
        numero2 = Orcamento.gerar_proximo_numero(self.empresa)
        self.assertEqual(numero2, 'ORC-002')
        
        # Criar mais um
        Orcamento.objects.create(
            numero=numero2,
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste 2',
            status=self.st_padrao,
            usuario_criacao=self.usuario
        )
        
        # Próximo deve ser ORC-003
        numero3 = Orcamento.gerar_proximo_numero(self.empresa)
        self.assertEqual(numero3, 'ORC-003')
    
    def test_numero_unico(self):
        """Testa que número do orçamento deve ser único"""
        numero = Orcamento.gerar_proximo_numero(self.empresa)
        Orcamento.objects.create(
            numero=numero,
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_padrao,
            usuario_criacao=self.usuario
        )
        
        with self.assertRaises(Exception):
            Orcamento.objects.create(
                numero=numero,  # Tentar criar com mesmo número
                empresa=self.empresa,
                cliente=self.cliente,
                descricao='Teste 2',
                status=self.st_padrao,
                usuario_criacao=self.usuario
            )
    
    def test_atribuir_varios_status_configurados(self):
        """Orçamento pode receber qualquer registro de StatusOrcamento."""
        s1 = StatusOrcamento.objects.create(nome='Fase 1', ordem=1)
        s2 = StatusOrcamento.objects.create(nome='Fase 2', ordem=2)
        orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=s1,
            usuario_criacao=self.usuario
        )
        for st in (s1, s2):
            orcamento.status = st
            orcamento.save()
            self.assertEqual(orcamento.status_id, st.pk)
    
    def test_ordenacao_por_data_criacao(self):
        """Testa que orçamentos são ordenados por data de criação (mais recente primeiro)"""
        orcamento1 = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste 1',
            status=self.st_padrao,
            usuario_criacao=self.usuario
        )
        orcamento2 = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste 2',
            status=self.st_padrao,
            usuario_criacao=self.usuario
        )
        
        orcamentos = Orcamento.objects.all()
        self.assertEqual(orcamentos[0], orcamento2)  # Mais recente primeiro
        self.assertEqual(orcamentos[1], orcamento1)
    
    def test_str_representation(self):
        """Testa a representação em string do modelo"""
        numero = Orcamento.gerar_proximo_numero(self.empresa)
        orcamento = Orcamento.objects.create(
            numero=numero,
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_padrao,
            usuario_criacao=self.usuario
        )
        self.assertIn(numero, str(orcamento))
        self.assertIn(self.cliente.razao_social, str(orcamento))
    
    def test_calcular_valor_total(self):
        """Testa método calcular_valor_total"""
        orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_padrao,
            usuario_criacao=self.usuario
        )
        
        # Criar itens
        ItemOrcamento.objects.create(
            orcamento=orcamento,
            tipo='servico',
            descricao='Mão de obra',
            quantidade=2,
            valor_unitario=250.00
        )
        ItemOrcamento.objects.create(
            orcamento=orcamento,
            tipo='peca',
            descricao='Peça X',
            quantidade=1,
            valor_unitario=100.00
        )
        
        # Calcular valor total
        total = orcamento.calcular_valor_total()
        
        # Verificar valor total (2*250 + 1*100 = 600)
        self.assertEqual(float(total), 600.00)
        orcamento.refresh_from_db()
        self.assertEqual(float(orcamento.valor_total), 600.00)

    def test_calcular_valor_total_com_desconto_valor(self):
        """Testa cálculo com desconto em valor fixo"""
        orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_padrao,
            usuario_criacao=self.usuario,
            desconto=50.00,
            desconto_tipo='valor'
        )
        ItemOrcamento.objects.create(
            orcamento=orcamento,
            tipo='servico',
            descricao='Mão de obra',
            quantidade=2,
            valor_unitario=250.00
        )
        # Subtotal 500, desconto 50 -> total 450
        orcamento.calcular_valor_total()
        orcamento.refresh_from_db()
        self.assertEqual(float(orcamento.valor_total), 450.00)

    def test_calcular_valor_total_com_desconto_percentual(self):
        """Testa cálculo com desconto percentual"""
        orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_padrao,
            usuario_criacao=self.usuario,
            desconto=10,
            desconto_tipo='percentual'
        )
        ItemOrcamento.objects.create(
            orcamento=orcamento,
            tipo='servico',
            descricao='Serviço',
            quantidade=1,
            valor_unitario=1000.00
        )
        # Subtotal 1000, 10% desconto = 100 -> total 900
        orcamento.calcular_valor_total()
        orcamento.refresh_from_db()
        self.assertEqual(float(orcamento.valor_total), 900.00)

    def test_calcular_valor_total_com_acrescimo_valor(self):
        """Testa cálculo com acréscimo em valor fixo"""
        orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_padrao,
            usuario_criacao=self.usuario,
            acrescimo=25.00,
            acrescimo_tipo='valor'
        )
        ItemOrcamento.objects.create(
            orcamento=orcamento,
            tipo='servico',
            descricao='Serviço',
            quantidade=1,
            valor_unitario=100.00
        )
        # Subtotal 100, acréscimo 25 -> total 125
        orcamento.calcular_valor_total()
        orcamento.refresh_from_db()
        self.assertEqual(float(orcamento.valor_total), 125.00)

    def test_calcular_valor_total_com_desconto_e_acrescimo(self):
        """Testa cálculo com desconto e acréscimo combinados"""
        orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_padrao,
            usuario_criacao=self.usuario,
            desconto=10,
            desconto_tipo='percentual',
            acrescimo=5,
            acrescimo_tipo='percentual'
        )
        ItemOrcamento.objects.create(
            orcamento=orcamento,
            tipo='servico',
            descricao='Serviço',
            quantidade=1,
            valor_unitario=1000.00
        )
        # Subtotal 1000, -10% = 900, +5% sobre 900 = 45 -> total 945
        orcamento.calcular_valor_total()
        orcamento.refresh_from_db()
        self.assertEqual(float(orcamento.valor_total), 945.00)


class ItemOrcamentoModelTest(TestCase):
    """Testes para o modelo ItemOrcamento"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.usuario = User.objects.create_user(
            username='vendedor',
            password='testpass123'
        )
        self.empresa = criar_empresa(cnpj='55666777000181', razao_social='Empresa Item Teste')
        self.cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste',
            usuario_cadastro=self.usuario
        )
        self.st_item = criar_status('Item teste', ordem=1)
        self.orcamento = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_item,
            usuario_criacao=self.usuario
        )
    
    def test_criar_item_orcamento(self):
        """Testa criação de item de orçamento"""
        item = ItemOrcamento.objects.create(
            orcamento=self.orcamento,
            tipo='servico',
            descricao='Mão de obra',
            quantidade=2,
            valor_unitario=250.00
        )
        
        self.assertEqual(item.orcamento, self.orcamento)
        self.assertEqual(item.tipo, 'servico')
        self.assertEqual(item.descricao, 'Mão de obra')
        self.assertEqual(item.quantidade, 2)
        self.assertEqual(item.valor_unitario, 250.00)
        self.assertEqual(item.valor_total, 500.00)
    
    def test_valor_total_calculado(self):
        """Testa cálculo automático do valor total"""
        item = ItemOrcamento.objects.create(
            orcamento=self.orcamento,
            tipo='peca',
            descricao='Peça X',
            quantidade=3,
            valor_unitario=50.00
        )
        
        self.assertEqual(item.valor_total, 150.00)
    
    def test_str_representation(self):
        """Testa a representação em string do modelo"""
        item = ItemOrcamento.objects.create(
            orcamento=self.orcamento,
            tipo='servico',
            descricao='Serviço Y',
            quantidade=1,
            valor_unitario=100.00
        )
        self.assertIn('Serviço Y', str(item))
        self.assertIn('ORC-001', str(item))
    
    def test_cascade_delete(self):
        """Testa que itens são deletados quando orçamento é deletado"""
        item = ItemOrcamento.objects.create(
            orcamento=self.orcamento,
            tipo='servico',
            descricao='Teste',
            quantidade=1,
            valor_unitario=100.00
        )
        
        item_id = item.id
        self.orcamento.delete()
        
        self.assertFalse(ItemOrcamento.objects.filter(id=item_id).exists())
