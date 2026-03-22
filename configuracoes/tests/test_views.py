from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from clientes.models import Cliente
from ordens_servico.models import Orcamento
from ordens_servico.tests.support import criar_empresa, criar_status, definir_empresa_atual


class ConfiguracaoEmpresaViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            username='admin_cfg',
            password='testpass123',
        )
        self.empresa = criar_empresa(
            cnpj='33444555000181',
            razao_social='Empresa Config View',
        )
        definir_empresa_atual(self.usuario, self.empresa)
        self.client.force_authenticate(user=self.usuario)

    def test_listar_requer_autenticacao(self):
        self.client.force_authenticate(user=None)
        r = self.client.get('/api/v1/configuracoes-empresa/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_listar_retorna_paginacao(self):
        r = self.client.get('/api/v1/configuracoes-empresa/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('results', r.data)
        self.assertGreaterEqual(r.data['count'], 1)

    def test_criar_empresa(self):
        data = {
            'razao_social': 'Nova Empresa API',
            'cnpj': '44555666000181',
            'endereco': 'Rua Nova',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01310100',
        }
        r = self.client.post('/api/v1/configuracoes-empresa/', data, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['razao_social'], 'Nova Empresa API')

    def test_atualizar_empresa(self):
        r = self.client.patch(
            f'/api/v1/configuracoes-empresa/{self.empresa.id}/',
            {'razao_social': 'Nome Atualizado'},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['razao_social'], 'Nome Atualizado')
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.razao_social, 'Nome Atualizado')

    def test_deletar_com_orcamento_bloqueado(self):
        cl = Cliente.objects.create(
            cnpj_cpf='55666777000181',
            tipo_documento='CNPJ',
            razao_social='Cliente Del',
            usuario_cadastro=self.usuario,
        )
        st = criar_status('Cfg', ordem=1)
        Orcamento.objects.create(
            numero=Orcamento.gerar_proximo_numero(self.empresa),
            empresa=self.empresa,
            cliente=cl,
            usuario_criacao=self.usuario,
            descricao='X',
            status=st,
        )
        r = self.client.delete(f'/api/v1/configuracoes-empresa/{self.empresa.id}/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('erro', r.data)
