"""
Cobre permissões por módulo (não-staff) vs staff.
Combinações: só visualizar, cadastrar/configurar, sem acesso ao módulo, sem perfil.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from autenticacao.models import PerfilUsuario
from clientes.models import Cliente
from configuracoes.models import ConfiguracaoEmpresa
from ordens_servico.tests.support import criar_status


def _zerar_permissoes(perfil: PerfilUsuario) -> None:
    perfil.clientes_pode_visualizar = False
    perfil.clientes_pode_cadastrar = False
    perfil.orcamentos_pode_visualizar = False
    perfil.orcamentos_pode_cadastrar = False
    perfil.configuracoes_pode_visualizar = False
    perfil.configuracoes_pode_configurar = False
    perfil.save()


def _invalidar_cache_perfil_no_user(user: User) -> None:
    """Django guarda o reverse OneToOne em __dict__ e em _state.fields_cache."""
    user.__dict__.pop('perfil', None)
    state = getattr(user, '_state', None)
    if state is not None:
        fc = getattr(state, 'fields_cache', None)
        if isinstance(fc, dict):
            fc.pop('perfil', None)


def aplicar_permissoes(user: User, **kwargs) -> None:
    """Define flags do perfil (após zerar). Respeita implicações no save() do modelo."""
    perfil = PerfilUsuario.objects.get(user=user)
    _zerar_permissoes(perfil)
    perfil.refresh_from_db()
    for key, value in kwargs.items():
        setattr(perfil, key, value)
    perfil.save()
    _invalidar_cache_perfil_no_user(user)


def payload_empresa_completo(razao_social: str, cnpj_formatado: str) -> dict:
    """Campos obrigatórios do modelo ConfiguracaoEmpresa para POST."""
    return {
        'razao_social': razao_social,
        'cnpj': cnpj_formatado,
        'endereco': 'Rua Teste, 100',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cep': '01310100',
    }


class PermissoesStaffTestCase(TestCase):
    """Staff ignora restrições de módulo."""

    def setUp(self):
        self.client = APIClient()
        self.empresa = ConfiguracaoEmpresa.objects.create(
            razao_social='Empresa Staff',
            cnpj='11222333000181',
            endereco='Rua Staff',
            cidade='São Paulo',
            estado='SP',
            cep='01001000',
        )
        self.admin = User.objects.create_user(
            username='admin@t.com',
            email='admin@t.com',
            password='senha123456',
            is_staff=True,
        )
        p = PerfilUsuario.objects.get(user=self.admin)
        p.empresa_atual = self.empresa
        p.save(update_fields=['empresa_atual'])
        self.cliente = Cliente.objects.create(
            cnpj_cpf='99888777000166',
            tipo_documento='CNPJ',
            razao_social='Cliente Staff',
            usuario_cadastro=self.admin,
        )
        self.client.force_authenticate(user=self.admin)

    def test_staff_lista_e_cria_cliente(self):
        r = self.client.get('/api/v1/clientes/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r2 = self.client.post(
            '/api/v1/clientes/',
            {
                'cnpj_cpf': '55444333000122',
                'tipo_documento': 'CNPJ',
                'razao_social': 'Novo Cliente',
            },
            format='json',
        )
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)

    def test_staff_lista_usuarios(self):
        r = self.client.get('/api/v1/usuarios/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class PermissoesClientesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='u1@t.com',
            email='u1@t.com',
            password='senha123456',
            is_staff=False,
        )
        self.client.force_authenticate(user=self.user)
        self.cliente = Cliente.objects.create(
            cnpj_cpf='11111111000111',
            tipo_documento='CNPJ',
            razao_social='Cliente Existente',
            usuario_cadastro=self.user,
        )

    def test_sem_visualizar_nao_lista_clientes(self):
        aplicar_permissoes(self.user)
        r = self.client.get('/api/v1/clientes/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_somente_visualizar_lista_mas_nao_cria(self):
        aplicar_permissoes(self.user, clientes_pode_visualizar=True)
        r = self.client.get('/api/v1/clientes/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r2 = self.client.post(
            '/api/v1/clientes/',
            {
                'cnpj_cpf': '22222222000122',
                'tipo_documento': 'CNPJ',
                'razao_social': 'Novo',
            },
            format='json',
        )
        self.assertEqual(r2.status_code, status.HTTP_403_FORBIDDEN)

    def test_visualizar_ve_detalhe(self):
        aplicar_permissoes(self.user, clientes_pode_visualizar=True)
        r = self.client.get(f'/api/v1/clientes/{self.cliente.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_com_cadastrar_cria_cliente(self):
        aplicar_permissoes(
            self.user,
            clientes_pode_visualizar=True,
            clientes_pode_cadastrar=True,
        )
        r = self.client.post(
            '/api/v1/clientes/',
            {
                'cnpj_cpf': '33333333000133',
                'tipo_documento': 'CNPJ',
                'razao_social': 'Cliente Novo',
            },
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_consultar_cnpj_exige_cadastrar(self):
        aplicar_permissoes(self.user, clientes_pode_visualizar=True)
        r = self.client.get('/api/v1/clientes/consultar_cnpj/?cnpj=12345678000190')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


class PermissoesOrcamentosTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.empresa = ConfiguracaoEmpresa.objects.create(
            razao_social='Empresa Orç',
            cnpj='44555666000177',
            endereco='Rua Orç',
            cidade='São Paulo',
            estado='SP',
            cep='01001000',
        )
        self.user = User.objects.create_user(
            username='u2@t.com',
            email='u2@t.com',
            password='senha123456',
            is_staff=False,
        )
        p = PerfilUsuario.objects.get(user=self.user)
        p.empresa_atual = self.empresa
        p.save(update_fields=['empresa_atual'])
        self.cliente = Cliente.objects.create(
            cnpj_cpf='66666666000166',
            tipo_documento='CNPJ',
            razao_social='Cliente Orç',
            usuario_cadastro=self.user,
        )
        self.st_orc = criar_status('Perm orc', ordem=1)
        self.client.force_authenticate(user=self.user)

    def test_sem_visualizar_orcamentos(self):
        aplicar_permissoes(self.user)
        r = self.client.get('/api/v1/orcamentos/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_somente_visualizar_lista_sem_criar(self):
        aplicar_permissoes(self.user, orcamentos_pode_visualizar=True)
        r = self.client.get('/api/v1/orcamentos/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r2 = self.client.post(
            '/api/v1/orcamentos/',
            {
                'cliente': self.cliente.id,
                'descricao': 'Teste',
                'status': self.st_orc.id,
            },
            format='json',
        )
        self.assertEqual(r2.status_code, status.HTTP_403_FORBIDDEN)

    def test_com_cadastrar_cria_orcamento(self):
        aplicar_permissoes(
            self.user,
            orcamentos_pode_visualizar=True,
            orcamentos_pode_cadastrar=True,
        )
        r = self.client.post(
            '/api/v1/orcamentos/',
            {
                'cliente': self.cliente.id,
                'descricao': 'Novo orçamento',
                'status': self.st_orc.id,
            },
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)


class PermissoesConfiguracoesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        ConfiguracaoEmpresa.objects.create(
            razao_social='E1',
            cnpj='77888999000100',
            endereco='Rua A',
            cidade='São Paulo',
            estado='SP',
            cep='01001000',
        )
        self.user = User.objects.create_user(
            username='u3@t.com',
            email='u3@t.com',
            password='senha123456',
            is_staff=False,
        )
        self.client.force_authenticate(user=self.user)

    def test_sem_visualizar_config(self):
        aplicar_permissoes(self.user)
        r = self.client.get('/api/v1/configuracoes-empresa/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_somente_visualizar_lista_sem_criar_empresa(self):
        aplicar_permissoes(self.user, configuracoes_pode_visualizar=True)
        r = self.client.get('/api/v1/configuracoes-empresa/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r2 = self.client.post(
            '/api/v1/configuracoes-empresa/',
            payload_empresa_completo('Nova Empresa LTDA', '88.777.666/0001-55'),
            format='json',
        )
        self.assertEqual(r2.status_code, status.HTTP_403_FORBIDDEN)

    def test_com_configurar_cria_empresa(self):
        aplicar_permissoes(
            self.user,
            configuracoes_pode_visualizar=True,
            configuracoes_pode_configurar=True,
        )
        r = self.client.post(
            '/api/v1/configuracoes-empresa/',
            payload_empresa_completo('Nova Empresa Dois LTDA', '99.888.777/0001-44'),
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)


class PermissoesUsuariosCRUDTestCase(TestCase):
    """CRUD /api/usuarios/ só para staff."""

    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='s@t.com',
            email='s@t.com',
            password='senha123456',
            is_staff=True,
        )
        self.normal = User.objects.create_user(
            username='n@t.com',
            email='n@t.com',
            password='senha123456',
            is_staff=False,
        )
        aplicar_permissoes(
            self.normal,
            clientes_pode_visualizar=True,
            orcamentos_pode_visualizar=True,
            configuracoes_pode_visualizar=True,
        )

    def test_nao_staff_nao_lista_usuarios(self):
        self.client.force_authenticate(user=self.normal)
        r = self.client.get('/api/v1/usuarios/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_lista_usuarios(self):
        self.client.force_authenticate(user=self.staff)
        r = self.client.get('/api/v1/usuarios/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class SemPerfilUsuarioTestCase(TestCase):
    """Sem linha em PerfilUsuario: módulos negam (getattr retorna None após delete)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='nop@t.com',
            email='nop@t.com',
            password='senha123456',
            is_staff=False,
        )
        uid = self.user.pk
        PerfilUsuario.objects.filter(user_id=uid).delete()
        self.user = User.objects.get(pk=uid)
        _invalidar_cache_perfil_no_user(self.user)
        self.client.force_authenticate(user=self.user)

    def test_sem_perfil_clientes_negado(self):
        r = self.client.get('/api/v1/clientes/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
