"""
Serviços para integração com APIs externas
"""
import requests
import re


def consultar_cnpj_sefaz(cnpj):
    """
    Consulta dados de CNPJ na API da ReceitaWS (API pública para consulta de CNPJ).
    
    Args:
        cnpj: CNPJ sem formatação (apenas números)
    
    Returns:
        dict: Dados da empresa formatados
    """
    # Remove formatação
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # API pública gratuita para consulta de CNPJ
    # Alternativa: usar API da ReceitaWS ou similar
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Verifica se a consulta foi bem-sucedida
        if data.get('status') == 'ERROR':
            raise Exception(data.get('message', 'Erro ao consultar CNPJ'))
        
        # Formata os dados retornados
        ie_raw = data.get('ie') or data.get('inscricao_estadual') or ''
        email_raw = data.get('email') or ''
        dados_formatados = {
            'cnpj_cpf': data.get('cnpj', '').replace('.', '').replace('/', '').replace('-', ''),
            'tipo_documento': 'CNPJ',
            'razao_social': data.get('nome', ''),
            'nome_fantasia': data.get('fantasia', ''),
            'inscricao_estadual': str(ie_raw).strip() or '',
            'email': str(email_raw).strip() or '',
            'telefone': data.get('telefone', ''),
            'endereco': f"{data.get('logradouro', '')}, {data.get('numero', '')}".strip(', '),
            'cep': data.get('cep', '').replace('-', ''),
            'cidade': data.get('municipio', ''),
            'estado': data.get('uf', ''),
        }
        
        return dados_formatados
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro ao consultar API: {str(e)}")
    except Exception as e:
        raise Exception(f"Erro ao processar dados: {str(e)}")

