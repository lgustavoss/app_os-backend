"""Fluxos críticos: multi-empresa, paginação da API e PDF."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from clientes.models import Cliente
from ordens_servico.models import Orcamento
from ordens_servico.tests.support import criar_empresa, criar_status, definir_empresa_atual


class MultiEmpresaPaginacaoPDFTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='fluxo_user',
            password='senha123456',
            email='fluxo@example.com',
        )
        self.emp_a = criar_empresa(cnpj='10111222000181', razao_social='Empresa Fluxo A')
        self.emp_b = criar_empresa(cnpj='10111222000262', razao_social='Empresa Fluxo B')
        definir_empresa_atual(self.user, self.emp_a)
        self.cli = Cliente.objects.create(
            cnpj_cpf='20111222000181',
            tipo_documento='CNPJ',
            razao_social='Cliente Fluxo',
            usuario_cadastro=self.user,
        )
        self.st_fluxo = criar_status('Fluxo', ordem=1)
        self.o_a = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.emp_a),
            empresa=self.emp_a,
            cliente=self.cli,
            usuario_criacao=self.user,
            descricao='Orçamento A',
            status=self.st_fluxo,
        )
        self.o_b = Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.emp_b),
            empresa=self.emp_b,
            cliente=self.cli,
            usuario_criacao=self.user,
            descricao='Orçamento B',
            status=self.st_fluxo,
        )
        self.client.force_authenticate(user=self.user)

    def test_listagem_respeita_empresa_atual(self):
        r = self.client.get('/api/v1/orcamentos/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ids = {row['id'] for row in r.data['results']}
        self.assertIn(self.o_a.id, ids)
        self.assertNotIn(self.o_b.id, ids)

    def test_troca_empresa_altera_orcamentos_visiveis(self):
        r = self.client.patch(
            '/api/v1/auth/user/',
            {'empresa_atual': self.emp_b.id},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # Novo pedido com utilizador recarregado (evita cache do OneToOne perfil no mesmo objeto User)
        from django.contrib.auth import get_user_model

        fresh = get_user_model().objects.get(pk=self.user.pk)
        self.client.force_authenticate(user=fresh)
        r2 = self.client.get('/api/v1/orcamentos/')
        ids = {row['id'] for row in r2.data['results']}
        self.assertNotIn(self.o_a.id, ids)
        self.assertIn(self.o_b.id, ids)

    def test_paginacao_page_size_padrao(self):
        for i in range(20):
            Orcamento.objects.create(
                numero=Orcamento.gerar_proximo_numero(self.emp_a),
                empresa=self.emp_a,
                cliente=self.cli,
                usuario_criacao=self.user,
                descricao=f'Bulk {i}',
                status=self.st_fluxo,
            )
        r1 = self.client.get('/api/v1/orcamentos/')
        self.assertEqual(r1.data['count'], 21)
        self.assertEqual(len(r1.data['results']), 20)
        r2 = self.client.get('/api/v1/orcamentos/?page=2')
        self.assertEqual(len(r2.data['results']), 1)

    def test_gerar_pdf_via_api(self):
        r = self.client.get(f'/api/v1/orcamentos/{self.o_a.id}/gerar_pdf/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertIn(b'%PDF', r.content)


class OpenAPISchemaTest(TestCase):
    def test_schema_v1_disponivel(self):
        r = APIClient().get('/api/v1/schema/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        body = r.content.decode('utf-8')
        self.assertIn('openapi', body.lower())
