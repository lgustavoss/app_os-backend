from django.test import TestCase

from configuracoes.models import ConfiguracaoEmpresa


class ConfiguracaoEmpresaModelTest(TestCase):
    """Modelo multi-empresa (sem singleton)."""

    def test_criar_campos_obrigatorios(self):
        e = ConfiguracaoEmpresa.objects.create(
            razao_social='Empresa X',
            cnpj='11222333000181',
            endereco='Rua A',
            cidade='São Paulo',
            estado='SP',
            cep='01001000',
        )
        self.assertEqual(e.razao_social, 'Empresa X')
        self.assertTrue(e.pk)

    def test_str_usa_razao_social(self):
        e = ConfiguracaoEmpresa.objects.create(
            razao_social='Nome Ltda',
            cnpj='22333444000181',
            endereco='Rua B',
            cidade='Campinas',
            estado='SP',
            cep='13000000',
        )
        self.assertIn('Nome Ltda', str(e))
