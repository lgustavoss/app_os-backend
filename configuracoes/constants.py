"""
Constantes para configurações da empresa.
"""

# Dimensões máximas da logomarca no PDF (em centímetros)
# A logo é exibida no canto superior esquerdo do orçamento.
# O frontend deve usar estas dimensões como tamanho máximo ao importar
# e permitir que o usuário ajuste (diminuir/aumentar) para otimizar a visualização.
LOGO_LARGURA_MAX_CM = 2.5
LOGO_ALTURA_MAX_CM = 2.5

# Faixa de selos no PDF: mesma altura da logo; cada imagem em um “slot” com proporção contida.
# Para melhor resultado, use artes em que o conteúdo importante caiba em formato próximo de
# quadrado ou retrato (evite banners muito largos e baixos). Até 3 selos lado a lado.
SELO_COLUNA_LARGURA_CM = 5.5
# Largura média por slot (apenas referência para o front / orientação ao usuário)
SELO_LARGURA_MAX_CM = 1.75
SELO_ALTURA_MAX_CM = LOGO_ALTURA_MAX_CM
