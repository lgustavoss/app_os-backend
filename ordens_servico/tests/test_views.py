from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from clientes.models import Cliente
from ordens_servico.models import HistoricoStatusOrcamento, Orcamento, ItemOrcamento
from produtos.models import Produto
from ordens_servico.tests.support import criar_empresa, definir_empresa_atual, criar_status


class OrcamentoViewSetTest(TestCase):
    """Testes para o ViewSet de Orçamentos"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            username='vendedor',
            password='testpass123'
        )
        self.empresa = criar_empresa()
        definir_empresa_atual(self.usuario, self.empresa)
        self.client.force_authenticate(user=self.usuario)
        
        self.cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste Ltda',
            usuario_cadastro=self.usuario
        )

        self.st_a = criar_status('Rascunho', ordem=1)
        self.st_b = criar_status('Enviado', ordem=2)

        n1 = Orcamento.gerar_proximo_numero(self.empresa)
        self.orcamento1 = Orcamento.objects.create(
            numero=n1,
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Serviços de manutenção',
            status=self.st_a,
            usuario_criacao=self.usuario
        )
        n2 = Orcamento.gerar_proximo_numero(self.empresa)
        self.orcamento2 = Orcamento.objects.create(
            numero=n2,
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Reparo de equipamento',
            status=self.st_b,
            usuario_criacao=self.usuario
        )
        HistoricoStatusOrcamento.objects.create(
            orcamento=self.orcamento1,
            usuario=self.usuario,
            status_anterior=None,
            status_novo=self.st_a,
            origem=HistoricoStatusOrcamento.Origem.CRIACAO,
        )
        HistoricoStatusOrcamento.objects.create(
            orcamento=self.orcamento2,
            usuario=self.usuario,
            status_anterior=None,
            status_novo=self.st_b,
            origem=HistoricoStatusOrcamento.Origem.CRIACAO,
        )

    def test_listar_ordens_requer_autenticacao(self):
        """Testa que listagem requer autenticação"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/orcamentos/')
        
        # IsAuthenticated retorna 403, não 401
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_listar_orcamentos(self):
        """Testa listagem de orçamentos"""
        response = self.client.get('/api/v1/orcamentos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_obter_detalhes_ordem_servico(self):
        """Testa obtenção de detalhes de um orçamento"""
        response = self.client.get(f'/api/v1/orcamentos/{self.orcamento1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('numero', response.data)
        self.assertTrue(response.data['numero'].startswith('ORC-'))
        self.assertEqual(response.data['cliente'], self.cliente.id)
        hist = response.data.get('historico_status')
        self.assertIsNotNone(hist)
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]['origem'], 'criacao')
        self.assertIsNone(hist[0]['status_anterior'])
        self.assertEqual(hist[0]['status_novo'], self.st_a.id)
    
    def test_criar_orcamento_sem_descricao(self):
        """Testa criação de orçamento sem descrição (campo opcional)"""
        data = {'cliente': self.cliente.id, 'status': self.st_a.id}
        response = self.client.post('/api/v1/orcamentos/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('numero', response.data)
        self.assertIsNone(response.data.get('descricao'))

    def test_criar_ordem_servico(self):
        """Testa criação de novo orçamento com numeração automática"""
        data = {
            'cliente': self.cliente.id,
            'descricao': 'Novo orçamento',
            'status': self.st_a.id,
        }
        
        response = self.client.post('/api/v1/orcamentos/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verificar que número foi gerado automaticamente
        self.assertIn('numero', response.data)
        self.assertTrue(response.data['numero'].startswith('ORC-'))
        self.assertEqual(response.data['cliente'], self.cliente.id)
        # Verificar que retorna dados completos após criação
        self.assertIn('data_criacao', response.data)
        self.assertEqual(response.data['usuario_criacao'], self.usuario.id)
    
    def test_numero_sequencial_automatico(self):
        """Testa que números são gerados sequencialmente"""
        # Criar primeiro orçamento
        data1 = {
            'cliente': self.cliente.id,
            'descricao': 'Orçamento 1',
            'status': self.st_a.id,
        }
        response1 = self.client.post('/api/v1/orcamentos/', data1, format='json')
        numero1 = response1.data['numero']
        
        # Criar segundo orçamento
        data2 = {
            'cliente': self.cliente.id,
            'descricao': 'Orçamento 2',
            'status': self.st_a.id,
        }
        response2 = self.client.post('/api/v1/orcamentos/', data2, format='json')
        numero2 = response2.data['numero']
        
        # Verificar que são sequenciais
        self.assertNotEqual(numero1, numero2)
        # Extrair números sequenciais
        num1 = int(numero1.split('-')[1])
        num2 = int(numero2.split('-')[1])
        self.assertEqual(num2, num1 + 1)
    
    def test_criar_orcamento_com_itens(self):
        """Testa criação de orçamento já com itens"""
        Produto.objects.create(codigo=1, descricao='Peça X', valor=100)
        data = {
            'cliente': self.cliente.id,
            'descricao': 'Orçamento com itens',
            'status': self.st_a.id,
            'itens': [
                {
                    'tipo': 'servico',
                    'descricao': 'Mão de obra',
                    'quantidade': 2,
                    'valor_unitario': '250.00'
                },
                {
                    'tipo': 'peca',
                    'produto': 1,
                    'descricao': 'Peça X',
                    'quantidade': 1,
                    'valor_unitario': '100.00'
                }
            ]
        }
        
        response = self.client.post('/api/v1/orcamentos/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verificar que número foi gerado automaticamente
        self.assertIn('numero', response.data)
        self.assertTrue(response.data['numero'].startswith('ORC-'))
        self.assertEqual(response.data['cliente'], self.cliente.id)
        self.assertEqual(len(response.data['itens']), 2)
        # Verificar que valor total foi calculado
        self.assertEqual(float(response.data['valor_total']), 600.00)
        # Verificar itens
        self.assertEqual(response.data['itens'][0]['descricao'], 'Mão de obra')
        self.assertEqual(response.data['itens'][0]['tipo'], 'servico')
        self.assertEqual(response.data['itens'][1]['descricao'], 'Peça X')
        self.assertEqual(response.data['itens'][1]['tipo'], 'peca')
        self.assertEqual(response.data['itens'][1]['produto'], 1)

    def test_criar_orcamento_com_desconto_acrescimo(self):
        """Testa criação de orçamento com desconto e acréscimo"""
        data = {
            'cliente': self.cliente.id,
            'descricao': 'Orçamento com desconto',
            'status': self.st_a.id,
            'desconto': '10',
            'desconto_tipo': 'percentual',
            'acrescimo': '0',
            'acrescimo_tipo': 'valor',
            'itens': [
                {'tipo': 'servico', 'descricao': 'Serviço', 'quantidade': 1, 'valor_unitario': '1000.00'}
            ]
        }
        response = self.client.post('/api/v1/orcamentos/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Subtotal 1000, 10% desconto = 900
        self.assertEqual(float(response.data['subtotal']), 1000.00)
        self.assertEqual(float(response.data['valor_desconto_calculado']), 100.00)
        self.assertEqual(float(response.data['valor_total']), 900.00)
        self.assertIn('desconto', response.data)
        self.assertIn('acrescimo', response.data)
    
    def test_atualizar_desconto_recalcula_total(self):
        """Testa que PATCH em desconto recalcula valor_total"""
        ItemOrcamento.objects.create(
            orcamento=self.orcamento1,
            tipo='servico',
            descricao='Mão de obra',
            quantidade=2,
            valor_unitario=250.00
        )
        self.orcamento1.calcular_valor_total()  # total 500
        response = self.client.patch(
            f'/api/v1/orcamentos/{self.orcamento1.id}/',
            {'desconto': '50', 'desconto_tipo': 'valor'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['valor_total']), 450.00)
    
    def test_listar_por_cliente_todas_empresas(self):
        """Detalhe do cliente: lista orçamentos do cliente em todas as empresas."""
        outra = criar_empresa(
            razao_social='Empresa B Ltda',
            cnpj='88777666000155',
        )
        n_b = Orcamento.gerar_proximo_numero(outra)
        Orcamento.objects.create(
            numero=n_b,
            empresa=outra,
            cliente=self.cliente,
            status=self.st_a,
            usuario_criacao=self.usuario,
        )
        url = (
            f'/api/v1/orcamentos/?cliente={self.cliente.id}'
            '&todas_empresas=true&incluir_excluidos=true'
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        empresas_ids = {row['empresa'] for row in response.data['results']}
        self.assertIn(self.empresa.id, empresas_ids)
        self.assertIn(outra.id, empresas_ids)
        nomes = {row.get('empresa_nome') for row in response.data['results']}
        self.assertIn('Empresa B Ltda', nomes)

    def test_listar_por_cliente_sem_todas_empresas_respeita_empresa_atual(self):
        outra = criar_empresa(
            razao_social='Empresa B Ltda',
            cnpj='88777666000155',
        )
        Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(outra),
            empresa=outra,
            cliente=self.cliente,
            status=self.st_a,
            usuario_criacao=self.usuario,
        )
        response = self.client.get(
            f'/api/v1/orcamentos/?cliente={self.cliente.id}&incluir_excluidos=true'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_retrieve_orcamento_de_outra_empresa(self):
        outra = criar_empresa(
            razao_social='Empresa B Ltda',
            cnpj='88777666000155',
        )
        o_other = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(outra),
            empresa=outra,
            cliente=self.cliente,
            status=self.st_a,
            usuario_criacao=self.usuario,
        )
        response = self.client.get(f'/api/v1/orcamentos/{o_other.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], o_other.id)
        self.assertEqual(response.data['empresa'], outra.id)

    def test_filtrar_por_status(self):
        """Testa filtro por id do status configurável"""
        response = self.client.get(f'/api/v1/orcamentos/?status={self.st_a.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['status'], self.st_a.id)

    def test_busca_por_status_texto(self):
        """Busca unificada por rótulo de status"""
        response = self.client.get('/api/v1/orcamentos/?search=Enviado')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.orcamento2.id)

    def test_busca_por_razao_social_cliente(self):
        response = self.client.get('/api/v1/orcamentos/?search=Teste')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_busca_por_numero(self):
        response = self.client.get(
            f'/api/v1/orcamentos/?search={self.orcamento1.numero}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.orcamento1.id)

    def test_busca_respeita_empresa(self):
        """Orçamentos de outra empresa não entram na busca"""
        outra = criar_empresa(
            razao_social='Outra SA',
            cnpj='99888777000166',
        )
        outro_cliente = Cliente.objects.create(
            cnpj_cpf='98765432000111',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste Ltda',
            usuario_cadastro=self.usuario,
        )
        Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(outra),
            empresa=outra,
            cliente=outro_cliente,
            status=self.st_a,
            usuario_criacao=self.usuario,
        )
        response = self.client.get('/api/v1/orcamentos/?search=Teste')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_adicionar_item_ordem_servico(self):
        """Testa adição de item ao orçamento"""
        data = {
            'tipo': 'servico',
            'descricao': 'Mão de obra',
            'quantidade': 2,
            'valor_unitario': '250.00'
        }
        
        response = self.client.post(
            f'/api/v1/orcamentos/{self.orcamento1.id}/adicionar_item/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['descricao'], 'Mão de obra')
        self.assertEqual(response.data['tipo'], 'servico')
        self.assertEqual(float(response.data['valor_total']), 500.00)
    
    def test_atualizar_status_ordem_servico(self):
        """Testa atualização de status do orçamento"""
        data = {
            'status': self.st_b.id,
        }

        response = self.client.patch(
            f'/api/v1/orcamentos/{self.orcamento1.id}/atualizar_status/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], self.st_b.id)

        self.orcamento1.refresh_from_db()
        self.assertEqual(self.orcamento1.status_id, self.st_b.id)

        detail = self.client.get(f'/api/v1/orcamentos/{self.orcamento1.id}/')
        hist = detail.data['historico_status']
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[-1]['origem'], 'atualizar_status')
        self.assertEqual(hist[-1]['status_anterior'], self.st_a.id)
        self.assertEqual(hist[-1]['status_novo'], self.st_b.id)

    def test_criar_orcamento_registra_historico_criacao(self):
        data = {
            'cliente': self.cliente.id,
            'descricao': 'Com histórico',
            'status': self.st_a.id,
        }
        r = self.client.post('/api/v1/orcamentos/', data, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        oid = r.data['id']
        d = self.client.get(f'/api/v1/orcamentos/{oid}/')
        hist = d.data['historico_status']
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]['origem'], 'criacao')

    def test_patch_orcamento_muda_status_registra_edicao(self):
        data = {'status': self.st_b.id}
        r = self.client.patch(
            f'/api/v1/orcamentos/{self.orcamento1.id}/',
            data,
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        d = self.client.get(f'/api/v1/orcamentos/{self.orcamento1.id}/')
        hist = d.data['historico_status']
        self.assertTrue(any(x['origem'] == 'edicao' for x in hist))

    def test_atualizar_status_null_retorna_erro(self):
        response = self.client.patch(
            f'/api/v1/orcamentos/{self.orcamento1.id}/atualizar_status/',
            {'status': None},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('erro', response.data)
        self.orcamento1.refresh_from_db()
        self.assertEqual(self.orcamento1.status_id, self.st_a.id)

    def test_criar_orcamento_sem_status_retorna_erro(self):
        response = self.client.post(
            '/api/v1/orcamentos/',
            {'cliente': self.cliente.id, 'descricao': 'X'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_atualizar_status_invalido(self):
        """Testa atualização com status inválido"""
        data = {
            'status': 999_999,
        }
        
        response = self.client.patch(
            f'/api/v1/orcamentos/{self.orcamento1.id}/atualizar_status/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('erro', response.data)
    
    def test_calcular_valor_total_automatico(self):
        """Testa que valor total é recalculado ao adicionar item"""
        # Adicionar primeiro item
        data1 = {
            'tipo': 'servico',
            'descricao': 'Mão de obra',
            'quantidade': 2,
            'valor_unitario': '250.00'
        }
        self.client.post(
            f'/api/v1/orcamentos/{self.orcamento1.id}/adicionar_item/',
            data1,
            format='json'
        )
        
        Produto.objects.create(codigo=1, descricao='Peça X', valor=100)
        # Adicionar segundo item
        data2 = {
            'tipo': 'peca',
            'produto': 1,
            'descricao': 'Peça X',
            'quantidade': 1,
            'valor_unitario': '100.00'
        }
        self.client.post(
            f'/api/v1/orcamentos/{self.orcamento1.id}/adicionar_item/',
            data2,
            format='json'
        )
        
        # Verificar valor total
        self.orcamento1.refresh_from_db()
        self.assertEqual(float(self.orcamento1.valor_total), 600.00)
    
    def test_gerar_orcamento_pdf(self):
        """Testa geração de PDF do orçamento"""
        response = self.client.get(f'/api/v1/orcamentos/{self.orcamento1.id}/gerar_pdf/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(self.orcamento1.numero, response['Content-Disposition'])
    
    def test_gerar_orcamento_requer_autenticacao(self):
        """Testa que geração de PDF requer autenticação"""
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/v1/orcamentos/{self.orcamento1.id}/gerar_pdf/')
        
        # IsAuthenticated retorna 403, não 401
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_deletar_ordem_servico(self):
        """Soft delete: orçamento permanece no BD com ativo=False"""
        response = self.client.delete(f'/api/v1/orcamentos/{self.orcamento1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.orcamento1.refresh_from_db()
        self.assertFalse(self.orcamento1.ativo)


class ItemOrcamentoViewSetTest(TestCase):
    """Testes para o ViewSet de Itens de Orçamento"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            username='vendedor',
            password='testpass123'
        )
        self.empresa = criar_empresa(cnpj='22333444000181', razao_social='Empresa Itens')
        definir_empresa_atual(self.usuario, self.empresa)
        self.client.force_authenticate(user=self.usuario)
        
        self.cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Empresa Teste',
            usuario_cadastro=self.usuario
        )
        
        num = Orcamento.gerar_proximo_numero(self.empresa)
        self.st_it = criar_status('Itens VS', ordem=1)
        self.orcamento = Orcamento.objects.create(
            numero=num,
            empresa=self.empresa,
            cliente=self.cliente,
            descricao='Teste',
            status=self.st_it,
            usuario_criacao=self.usuario
        )
        self.prod_item = Produto.objects.create(codigo=1, descricao='Peça X', valor=100)
        self.item1 = ItemOrcamento.objects.create(
            orcamento=self.orcamento,
            tipo='servico',
            descricao='Mão de obra',
            quantidade=2,
            valor_unitario=250.00
        )
        self.item2 = ItemOrcamento.objects.create(
            orcamento=self.orcamento,
            tipo='peca',
            descricao='Peça X',
            quantidade=1,
            valor_unitario=100.00,
            produto=self.prod_item,
        )
    
    def test_listar_itens_servico(self):
        """Testa listagem de itens de orçamento"""
        response = self.client.get('/api/v1/itens-orcamento/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_criar_item_servico(self):
        """Testa criação de item de orçamento"""
        data = {
            'orcamento': self.orcamento.id,
            'tipo': 'servico',
            'descricao': 'Novo serviço',
            'quantidade': 1,
            'valor_unitario': '150.00'
        }
        
        response = self.client.post('/api/v1/itens-orcamento/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['descricao'], 'Novo serviço')
        self.assertEqual(float(response.data['valor_total']), 150.00)
    
    def test_atualizar_item_servico(self):
        """Testa atualização de item de orçamento"""
        data = {
            'quantidade': 3
        }
        
        response = self.client.patch(
            f'/api/v1/itens-orcamento/{self.item1.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantidade'], 3)
        self.assertEqual(float(response.data['valor_total']), 750.00)
