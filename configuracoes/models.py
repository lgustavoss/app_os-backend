from django.db import models
from django.core.validators import FileExtensionValidator


class ConfiguracaoEmpresa(models.Model):
    """
    Modelo para armazenar as configurações de cada empresa (multi-empresa).
    Cada empresa tem sua própria configuração (dados, logomarca, textos).
    """
    
    razao_social = models.CharField(max_length=200, verbose_name='Razão Social')
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True, verbose_name='Nome Fantasia')
    nome_exibicao_menu = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Nome de exibição no menu',
        help_text='Nome curto no seletor de empresa. Se vazio, usa nome fantasia ou razão social.',
    )
    cnpj = models.CharField(max_length=18, verbose_name='CNPJ')
    inscricao_estadual = models.CharField(max_length=20, blank=True, null=True, verbose_name='Inscrição Estadual')
    inscricao_municipal = models.CharField(max_length=20, blank=True, null=True, verbose_name='Inscrição Municipal')
    
    # Endereço
    endereco = models.CharField(max_length=200, verbose_name='Endereço')
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name='Número')
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name='Complemento')
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name='Bairro')
    cidade = models.CharField(max_length=100, verbose_name='Cidade')
    estado = models.CharField(max_length=2, verbose_name='Estado')
    cep = models.CharField(max_length=10, verbose_name='CEP')
    
    # Contato
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    celular = models.CharField(max_length=20, blank=True, null=True, verbose_name='Celular')
    email = models.EmailField(blank=True, null=True, verbose_name='E-mail')
    website = models.URLField(blank=True, null=True, verbose_name='Website')
    
    # Logomarca (upload por empresa para não sobrescrever)
    logomarca = models.ImageField(
        upload_to='configuracoes/empresa/',
        blank=True,
        null=True,
        verbose_name='Logomarca',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )

    selo_certificacao_1 = models.ImageField(
        upload_to='configuracoes/empresa/selos/',
        blank=True,
        null=True,
        verbose_name='Selo de certificação 1 (PDF)',
        help_text='Ex.: NCC, INMETRO — aparece no topo direito do orçamento.',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
    )
    selo_certificacao_2 = models.ImageField(
        upload_to='configuracoes/empresa/selos/',
        blank=True,
        null=True,
        verbose_name='Selo de certificação 2 (PDF)',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
    )
    selo_certificacao_3 = models.ImageField(
        upload_to='configuracoes/empresa/selos/',
        blank=True,
        null=True,
        verbose_name='Selo de certificação 3 (PDF)',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
    )
    texto_selos_cabecalho_pdf = models.CharField(
        max_length=400,
        blank=True,
        default='',
        verbose_name='Texto no cabeçalho do PDF (sem selos)',
        help_text='Usado no topo direito quando não há imagens de selo (ex.: frase de certificação).',
    )

    # Informações adicionais para o orçamento
    texto_rodape = models.TextField(
        blank=True,
        null=True,
        verbose_name='Texto do Rodapé',
        help_text='Texto que aparecerá no rodapé do orçamento (ex: condições de pagamento)'
    )
    observacoes_padrao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observações Padrão',
        help_text='Observações que aparecerão por padrão nos orçamentos'
    )
    
    # Data de criação e atualização
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Configuração da Empresa'
        verbose_name_plural = 'Configurações da Empresa'
    
    def __str__(self):
        return self.razao_social or 'Configuração da Empresa'

