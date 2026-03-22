from django.test import TestCase
from unittest.mock import patch, Mock
from clientes.services import consultar_cnpj_sefaz


class ConsultarCNPJServiceTest(TestCase):
    """Testes para o serviço de consulta de CNPJ"""
    
    @patch('clientes.services.requests.get')
    def test_consultar_cnpj_sucesso(self, mock_get):
        """Testa consulta de CNPJ bem-sucedida"""
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.json.return_value = {
            'cnpj': '12.345.678/0001-90',
            'nome': 'Empresa Teste Ltda',
            'fantasia': 'Teste',
            'ie': '123.456.789.012',
            'email': 'contato@empresa.com.br',
            'telefone': '(11) 1234-5678',
            'logradouro': 'Rua Teste',
            'numero': '123',
            'cep': '01234-567',
            'municipio': 'São Paulo',
            'uf': 'SP'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        resultado = consultar_cnpj_sefaz('12345678000190')
        
        self.assertEqual(resultado['cnpj_cpf'], '12345678000190')
        self.assertEqual(resultado['tipo_documento'], 'CNPJ')
        self.assertEqual(resultado['razao_social'], 'Empresa Teste Ltda')
        self.assertEqual(resultado['nome_fantasia'], 'Teste')
        self.assertEqual(resultado['cidade'], 'São Paulo')
        self.assertEqual(resultado['estado'], 'SP')
        self.assertEqual(resultado['inscricao_estadual'], '123.456.789.012')
        self.assertEqual(resultado['email'], 'contato@empresa.com.br')
    
    @patch('clientes.services.requests.get')
    def test_consultar_cnpj_erro_api(self, mock_get):
        """Testa tratamento de erro da API"""
        mock_get.side_effect = Exception('Erro de conexão')
        
        with self.assertRaises(Exception) as context:
            consultar_cnpj_sefaz('12345678000190')
        
        # A mensagem pode variar, mas deve conter "Erro"
        self.assertIn('Erro', str(context.exception))
    
    @patch('clientes.services.requests.get')
    def test_consultar_cnpj_status_error(self, mock_get):
        """Testa tratamento quando API retorna erro"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'ERROR',
            'message': 'CNPJ não encontrado'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            consultar_cnpj_sefaz('12345678000190')
        
        self.assertIn('CNPJ não encontrado', str(context.exception))
    
    def test_consultar_cnpj_remove_formatacao(self):
        """Testa que remove formatação do CNPJ"""
        with patch('clientes.services.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'cnpj': '12.345.678/0001-90',
                'nome': 'Empresa Teste',
                'fantasia': '',
                'telefone': '',
                'logradouro': '',
                'numero': '',
                'cep': '',
                'municipio': '',
                'uf': ''
            }
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            resultado = consultar_cnpj_sefaz('12.345.678/0001-90')
            
            # Verifica que o CNPJ foi limpo
            self.assertEqual(resultado['cnpj_cpf'], '12345678000190')

