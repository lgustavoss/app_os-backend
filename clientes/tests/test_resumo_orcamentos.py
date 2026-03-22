from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from autenticacao.models import PerfilUsuario
from clientes.models import Cliente
from ordens_servico.models import Orcamento
from ordens_servico.tests.support import criar_empresa, criar_status


class ResumoOrcamentosClienteTest(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.user = User.objects.create_user(
            username='u1',
            password='x',
        )
        self.api.force_authenticate(user=self.user)
        self.cliente = Cliente.objects.create(
            cnpj_cpf='12345678000190',
            tipo_documento='CNPJ',
            razao_social='Cliente Resumo SA',
            usuario_cadastro=self.user,
        )
        self.emp_a = criar_empresa(
            razao_social='Empresa A',
            cnpj='11222333000181',
            nome_exibicao_menu='Emp A',
        )
        self.emp_b = criar_empresa(
            razao_social='Empresa B Ltda',
            cnpj='99888777000166',
        )
        self.st_r = criar_status('Rascunho', ordem=1)
        self.st_ap = criar_status('Aprovado', ordem=2)
        self.st_env = criar_status('Enviado', ordem=3)
        Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.emp_a),
            empresa=self.emp_a,
            cliente=self.cliente,
            status=self.st_r,
            valor_total=100,
            usuario_criacao=self.user,
            ativo=True,
        )
        Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.emp_a),
            empresa=self.emp_a,
            cliente=self.cliente,
            status=self.st_ap,
            valor_total=200,
            usuario_criacao=self.user,
            ativo=True,
        )
        Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.emp_b),
            empresa=self.emp_b,
            cliente=self.cliente,
            status=self.st_env,
            valor_total=50,
            usuario_criacao=self.user,
            ativo=False,
        )

    def test_resumo_totals_e_agrupamentos(self):
        url = f'/api/v1/clientes/{self.cliente.id}/resumo-orcamentos/'
        r = self.api.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['total_quantidade'], 3)
        self.assertEqual(r.data['valor_total_geral'], '350.00')
        self.assertEqual(r.data['ativos']['quantidade'], 2)
        self.assertEqual(r.data['ativos']['valor_total'], '300.00')
        self.assertEqual(r.data['excluidos']['quantidade'], 1)
        self.assertEqual(r.data['excluidos']['valor_total'], '50.00')

        emp_nomes = {x['empresa_nome'] for x in r.data['por_empresa']}
        self.assertIn('Emp A', emp_nomes)
        self.assertIn('Empresa B Ltda', emp_nomes)

        st = {x['status']: x for x in r.data['por_status']}
        self.assertEqual(st[self.st_r.id]['quantidade'], 1)
        self.assertEqual(st[self.st_ap.id]['valor_total'], '200.00')

    def test_resumo_sem_permissao_orcamentos(self):
        perfil = PerfilUsuario.objects.get(user=self.user)
        perfil.orcamentos_pode_visualizar = False
        perfil.orcamentos_pode_cadastrar = False
        perfil.save()
        # Evita cache de user.perfil no mesmo objeto User usado pelo APIClient
        self.user = User.objects.get(pk=self.user.pk)
        self.api.force_authenticate(user=self.user)

        url = f'/api/v1/clientes/{self.cliente.id}/resumo-orcamentos/'
        r = self.api.get(url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
