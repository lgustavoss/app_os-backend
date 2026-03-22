from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from clientes.models import Cliente
from ordens_servico.models import Orcamento
from ordens_servico.tests.support import criar_empresa, definir_empresa_atual, criar_status


class DashboardResumoViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.empresa = criar_empresa(cnpj='66777888000181', razao_social='Empresa Dashboard')
        definir_empresa_atual(self.user, self.empresa)
        self.client.force_authenticate(user=self.user)

    def test_retorna_estrutura_correta(self):
        response = self.client.get('/api/v1/dashboard/resumo/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_orcamentos', response.data)
        self.assertIn('total_clientes', response.data)
        self.assertIn('orcamentos_recentes', response.data)

    def test_contadores_zerados_sem_dados(self):
        response = self.client.get('/api/v1/dashboard/resumo/')
        self.assertEqual(response.data['total_orcamentos'], 0)
        self.assertEqual(response.data['total_clientes'], 0)
        self.assertEqual(response.data['orcamentos_recentes'], [])

    def test_contadores_com_dados(self):
        cliente = Cliente.objects.create(
            cnpj_cpf='12.345.678/0001-90',
            tipo_documento='CNPJ',
            razao_social='Cliente Teste',
            usuario_cadastro=self.user,
        )

        st = criar_status('Em andamento', ordem=1)
        Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=cliente,
            descricao='Orçamento 1',
            status=st,
            usuario_criacao=self.user,
        )
        Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=cliente,
            descricao='Orçamento 2',
            status=st,
            usuario_criacao=self.user,
        )

        response = self.client.get('/api/v1/dashboard/resumo/')
        self.assertEqual(response.data['total_orcamentos'], 2)
        self.assertEqual(response.data['total_clientes'], 1)
        self.assertEqual(len(response.data['orcamentos_recentes']), 2)

    def test_requer_autenticacao(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/dashboard/resumo/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
