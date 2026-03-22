"""
Serviços para geração de documentos
"""
from io import BytesIO
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.http import HttpResponse
from django.conf import settings
from xml.sax.saxutils import escape
import os

# Espaçamentos e dimensões
SP = 0.2 * cm   # espaço pequeno
SM = 0.35 * cm  # espaço médio
SL = 0.5 * cm   # espaço grande
# Largura útil do conteúdo (A4: 21cm - margens 1.5cm cada lado = 18cm)
LARGURA_UTIL = 18 * cm


def _formatar_moeda(valor):
    """Formata valor em moeda brasileira: 1.234,56"""
    s = f"{float(valor):.2f}"
    parte_int, parte_dec = s.split('.')
    nova_int = ''
    for i, c in enumerate(reversed(parte_int)):
        if i > 0 and i % 3 == 0:
            nova_int = '.' + nova_int
        nova_int = c + nova_int
    return f"{nova_int},{parte_dec}"


def _formatar_cnpj(valor):
    """Formata CNPJ: XX.XXX.XXX/XXXX-XX"""
    if not valor:
        return valor
    nums = ''.join(c for c in str(valor) if c.isdigit())
    if len(nums) == 14:
        return f"{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:]}"
    return valor


def _formatar_cpf(valor):
    """Formata CPF: XXX.XXX.XXX-XX"""
    if not valor:
        return valor
    nums = ''.join(c for c in str(valor) if c.isdigit())
    if len(nums) == 11:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"
    return valor


def _formatar_documento(valor, tipo_documento):
    """Formata CNPJ ou CPF conforme o tipo"""
    if tipo_documento == 'CNPJ':
        return _formatar_cnpj(valor)
    return _formatar_cpf(valor)


def _formatar_telefone(valor):
    """Formata telefone: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX"""
    if not valor:
        return valor
    nums = ''.join(c for c in str(valor) if c.isdigit())
    if len(nums) == 11:
        return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    if len(nums) == 10:
        return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return valor


def _preparar_logo_para_pdf(caminho_arquivo, largura_cm, altura_cm):
    """
    Carrega a logo e garante exibição correta no PDF.
    Composita imagens com transparência sobre fundo branco para evitar
    áreas transparentes renderizadas em preto pelo ReportLab.
    """
    try:
        img = PILImage.open(caminho_arquivo).convert('RGBA')
    except Exception:
        return None
    fundo = PILImage.new('RGB', img.size, (255, 255, 255))
    fundo.paste(img, mask=img.split()[3])
    buffer = BytesIO()
    fundo.save(buffer, format='PNG')
    buffer.seek(0)
    return Image(buffer, width=largura_cm * cm, height=altura_cm * cm)


def _preparar_imagem_fit_em_caixa(caminho_arquivo, max_largura_cm, max_altura_cm):
    """
    Redimensiona a imagem para caber dentro da caixa (contain), mantendo proporção.
    """
    try:
        img = PILImage.open(caminho_arquivo).convert('RGBA')
    except Exception:
        return None
    wpx, hpx = img.size
    if hpx <= 0 or wpx <= 0:
        return None
    aspect = wpx / hpx
    h_cm = max_altura_cm
    w_cm = h_cm * aspect
    if w_cm > max_largura_cm:
        w_cm = max_largura_cm
        h_cm = w_cm / aspect
    fundo = PILImage.new('RGB', img.size, (255, 255, 255))
    fundo.paste(img, mask=img.split()[3])
    buffer = BytesIO()
    fundo.save(buffer, format='PNG')
    buffer.seek(0)
    return Image(buffer, width=w_cm * cm, height=h_cm * cm)


def _tabela_selos_slots(paths_selos, col_largura_cm, slot_altura_cm, gap_cm=None):
    """
    Uma linha de células: cada selo centralizado num slot com altura fixa (= logo),
    imagem em 'contain'. Alinha visualmente a faixa à altura da logomarca.
    """
    if not paths_selos:
        return None
    n = len(paths_selos)
    if gap_cm is None:
        # Menos espaço entre células quando há poucos selos (evita “vão” grande no meio)
        gap_cm = 0.05 if n <= 2 else 0.10
    w_slots = col_largura_cm - gap_cm * max(0, n - 1)
    slot_w_cm = w_slots / n
    row = []
    col_ws = [slot_w_cm * cm] * n
    for p in paths_selos:
        img = _preparar_imagem_fit_em_caixa(p, slot_w_cm, slot_altura_cm)
        if img:
            inner = Table(
                [[img]],
                colWidths=[slot_w_cm * cm],
                rowHeights=[slot_altura_cm * cm],
            )
            inner.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            row.append(inner)
        else:
            row.append(Spacer(slot_w_cm * cm, 0.1 * cm))
    tbl = Table([row], colWidths=col_ws)
    st_cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]
    for i in range(n - 1):
        st_cmds.append(('RIGHTPADDING', (i, 0), (i, 0), gap_cm * cm))
    st_cmds.append(('RIGHTPADDING', (n - 1, 0), (n - 1, 0), 0))
    tbl.setStyle(TableStyle(st_cmds))
    return tbl


def gerar_pdf_orcamento(orcamento):
    """
    Gera um PDF do orçamento usando os dados da empresa do orçamento.
    
    Args:
        orcamento: Instância de Orcamento (com empresa definida)
    
    Returns:
        HttpResponse com o PDF gerado
    """
    from configuracoes.constants import (
        LOGO_LARGURA_MAX_CM,
        LOGO_ALTURA_MAX_CM,
        SELO_COLUNA_LARGURA_CM,
    )

    empresa = orcamento.empresa
    texto_rodape_pdf = (empresa.texto_rodape or '').strip()

    buffer = BytesIO()
    # Margem inferior maior quando há rodapé (desenhado no canvas em todas as páginas)
    margem_inferior = 2.0 * cm if texto_rodape_pdf else 1.5 * cm
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.5 * cm,
        bottomMargin=margem_inferior,
    )
    
    # Container para os elementos do PDF
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    base_indent = {'leftIndent': 0, 'rightIndent': 0, 'firstLineIndent': 0}
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle', parent=styles['Heading2'],
        fontSize=9, textColor=colors.HexColor('#374151'),
        spaceBefore=10, spaceAfter=6, fontName='Helvetica-Bold', alignment=TA_LEFT, **base_indent
    )
    # Títulos de seção (minimalista)
    secao_titulo_style = ParagraphStyle(
        'SecaoTituloPDF', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#6b7280'),
        fontName='Helvetica-Bold', alignment=TA_LEFT,
        spaceBefore=4, spaceAfter=6, leading=11, **base_indent
    )
    cli_label_style = ParagraphStyle(
        'CliLabel', parent=styles['Normal'],
        fontSize=7, textColor=colors.HexColor('#6b7280'), alignment=TA_LEFT,
        leading=9, spaceAfter=0, **base_indent
    )
    cli_val_style = ParagraphStyle(
        'CliVal', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#111827'), alignment=TA_LEFT,
        leading=10, spaceAfter=0, **base_indent
    )
    normal_style = ParagraphStyle(
        'NormalCompact', parent=styles['Normal'],
        fontSize=9, spaceAfter=2, textColor=colors.black, alignment=TA_LEFT, **base_indent
    )
    empresa_style = ParagraphStyle(
        'EmpresaStyle', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#374151'), spaceAfter=4, leading=11,
        alignment=TA_LEFT, **base_indent
    )
    empresa_center_style = ParagraphStyle(
        'EmpresaCenterStyle', parent=empresa_style,
        alignment=TA_CENTER
    )
    empresa_nome_center_style = ParagraphStyle(
        'EmpresaNomeCenter', parent=styles['Normal'],
        fontSize=11, leading=13, textColor=colors.HexColor('#111827'),
        spaceAfter=5, alignment=TA_CENTER, fontName='Helvetica-Bold', **base_indent
    )
    # Título do orçamento abaixo do cabeçalho (destaque, centralizado na folha)
    titulo_orc_banner_style = ParagraphStyle(
        'TituloOrcBanner', parent=styles['Normal'],
        fontSize=17, leading=21, textColor=colors.HexColor('#111827'),
        fontName='Helvetica-Bold', alignment=TA_CENTER, spaceBefore=0, spaceAfter=6, **base_indent
    )
    validade_debaixo_selos_style = ParagraphStyle(
        'ValidadeDebaixoSelos', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#6b7280'),
        alignment=TA_RIGHT, spaceBefore=0, spaceAfter=2, leading=12, **base_indent
    )
    
    # --- Cabeçalho: [Logo] | [Dados Empresa centralizados] | [Dados Orçamento] ---
    col_logo = []
    if empresa.logomarca:
        try:
            logo_path = empresa.logomarca.path
            if os.path.exists(logo_path):
                logo_img = _preparar_logo_para_pdf(
                    logo_path, LOGO_LARGURA_MAX_CM, LOGO_ALTURA_MAX_CM
                )
                if logo_img:
                    col_logo.append(logo_img)
        except (ValueError, OSError):
            pass  # ignora se arquivo não existir ou path inválido
    
    col_empresa = []
    if empresa.razao_social:
        col_empresa.append(Paragraph(escape(empresa.razao_social), empresa_nome_center_style))
    info_parts = []
    if empresa.cnpj:
        info_parts.append(f"CNPJ: {_formatar_cnpj(empresa.cnpj)}")
    if empresa.inscricao_estadual:
        info_parts.append(f"IE: {empresa.inscricao_estadual}")
    if info_parts:
        col_empresa.append(Paragraph(" · ".join(info_parts), empresa_center_style))
    end_parts = []
    if empresa.endereco:
        end_parts.append(empresa.endereco)
        if empresa.numero:
            end_parts.append(f", {empresa.numero}")
        if empresa.bairro:
            end_parts.append(f" — {empresa.bairro}")
        if empresa.cidade and empresa.estado:
            end_parts.append(f" — {empresa.cidade}/{empresa.estado}")
        elif empresa.cidade:
            end_parts.append(f" — {empresa.cidade}")
        if empresa.cep:
            end_parts.append(f" — CEP {empresa.cep}")
    if end_parts:
        col_empresa.append(Paragraph(escape("".join(end_parts)), empresa_center_style))
    cont_parts = []
    if empresa.telefone:
        cont_parts.append(_formatar_telefone(empresa.telefone))
    if empresa.email:
        cont_parts.append(empresa.email)
    if cont_parts:
        col_empresa.append(Paragraph(escape(" · ".join(cont_parts)), empresa_center_style))

    num_esc = escape(str(orcamento.numero or ''))
    linha_titulo_orc = f'Orçamento Nº: {num_esc}'

    # Selos (imagens) ou texto alternativo na faixa direita
    paths_selos = []
    for f in (empresa.selo_certificacao_1, empresa.selo_certificacao_2, empresa.selo_certificacao_3):
        if not f:
            continue
        try:
            p = f.path
            if os.path.exists(p):
                paths_selos.append(p)
        except (ValueError, OSError):
            pass

    texto_selos = (empresa.texto_selos_cabecalho_pdf or '').strip()
    tem_imagens_selo = bool(paths_selos)
    n_selos = len(paths_selos)

    # Coluna direita: só o necessário com imagens (2 selos = menos largura, mais espaço p/ empresa)
    slot_unit_cm = SELO_COLUNA_LARGURA_CM / 3.0
    if tem_imagens_selo:
        gap_selo_cm = 0.05 if n_selos <= 2 else 0.10
        col_selos_cm = min(
            SELO_COLUNA_LARGURA_CM,
            n_selos * slot_unit_cm + max(0, n_selos - 1) * gap_selo_cm,
        )
        w_right = col_selos_cm * cm
    elif texto_selos:
        gap_selo_cm = None
        col_selos_cm = SELO_COLUNA_LARGURA_CM
        w_right = SELO_COLUNA_LARGURA_CM * cm
    else:
        gap_selo_cm = None
        col_selos_cm = SELO_COLUNA_LARGURA_CM
        w_right = 0

    w_logo = 3 * cm
    w_mid = LARGURA_UTIL - w_logo - w_right

    tbl_logo = Table([[p] for p in col_logo] if col_logo else [[' ']], colWidths=[w_logo])
    tbl_logo.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))

    if tem_imagens_selo:
        col_centro = list(col_empresa)
        tbl_centro = Table([[c] for c in col_centro] if col_centro else [[' ']], colWidths=[w_mid])
        tbl_centro.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))

        tbl_selos = _tabela_selos_slots(
            paths_selos, col_selos_cm, LOGO_ALTURA_MAX_CM, gap_cm=gap_selo_cm
        )
        tbl_dir = Table([[tbl_selos]], colWidths=[w_right])
        tbl_dir.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        header_tbl = Table([[tbl_logo, tbl_centro, tbl_dir]], colWidths=[w_logo, w_mid, w_right])
    elif texto_selos:
        tbl_empresa = Table([[p] for p in col_empresa] if col_empresa else [[' ']], colWidths=[w_mid])
        tbl_empresa.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        selo_txt_style = ParagraphStyle(
            'SeloTxtStyle', parent=styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#4b5563'), spaceAfter=8,
            alignment=TA_RIGHT, leading=11, **base_indent
        )
        col_direita_txt = [Paragraph(escape(texto_selos), selo_txt_style)]
        tbl_direita = Table([[c] for c in col_direita_txt], colWidths=[w_right])
        tbl_direita.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        header_tbl = Table([[tbl_logo, tbl_empresa, tbl_direita]], colWidths=[w_logo, w_mid, w_right])
    else:
        tbl_empresa = Table([[p] for p in col_empresa] if col_empresa else [[' ']], colWidths=[w_mid])
        tbl_empresa.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        header_tbl = Table([[tbl_logo, tbl_empresa]], colWidths=[w_logo, w_mid])

    header_style_cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ]
    if w_right > 0:
        header_style_cmds.append(('ALIGN', (2, 0), (2, 0), 'RIGHT'))
    header_tbl.setStyle(TableStyle(header_style_cmds))
    elements.append(header_tbl)

    # Espaço extra entre cabeçalho e título do orçamento
    elements.append(Spacer(1, SL + 0.15 * cm))

    # Título centralizado na largura útil da folha
    faixa_titulo = Table(
        [[Paragraph(linha_titulo_orc, titulo_orc_banner_style)]],
        colWidths=[LARGURA_UTIL],
    )
    faixa_titulo.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(faixa_titulo)

    # Validade alinhada à direita, na faixa onde ficam os selos (coluna direita do cabeçalho)
    if orcamento.data_validade:
        val_txt = (
            f"Válido até <b>{orcamento.data_validade.strftime('%d/%m/%Y')}</b>"
        )
        val_para = Paragraph(val_txt, validade_debaixo_selos_style)
        if w_right > 0:
            w_left_folga = LARGURA_UTIL - w_right
            faixa_validade = Table(
                [['', val_para]],
                colWidths=[w_left_folga, w_right],
            )
            faixa_validade.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(faixa_validade)
        else:
            elements.append(val_para)

    elements.append(
        HRFlowable(
            width='100%',
            thickness=0.5,
            color=colors.HexColor('#e5e7eb'),
            spaceBefore=6,
            spaceAfter=10,
        )
    )

    elements.append(Paragraph("Dados do cliente", secao_titulo_style))
    cliente = orcamento.cliente
    # Garante campos atualizados (ex.: IE/e-mail) e evita instância em cache desatualizada
    cliente.refresh_from_db()
    # Layout compacto em 4 colunas: menos linhas, mesclagem horizontal (melhor para impressão)
    w_c0, w_c1, w_c2, w_c3 = 2.15 * cm, 6.35 * cm, 2.0 * cm, 7.5 * cm
    fundo_lbl = colors.HexColor('#f3f4f6')
    cli_rows = []
    cli_spans = []

    nome_html = escape(cliente.razao_social or '—')
    if cliente.nome_fantasia:
        nome_html += (
            f"<br/><font size='7' color='#6b7280'>{escape(cliente.nome_fantasia)}</font>"
        )
    cli_rows.append(
        [
            Paragraph("Razão social", cli_label_style),
            Paragraph(nome_html, cli_val_style),
            '',
            '',
        ]
    )
    cli_spans.append(('SPAN', (1, 0), (3, 0)))

    doc_lbl = escape(cliente.tipo_documento or 'Documento')
    doc_val = escape(_formatar_documento(cliente.cnpj_cpf, cliente.tipo_documento) or '—')
    if cliente.telefone:
        cli_rows.append(
            [
                Paragraph(doc_lbl, cli_label_style),
                Paragraph(doc_val, cli_val_style),
                Paragraph("Telefone", cli_label_style),
                Paragraph(escape(_formatar_telefone(cliente.telefone)), cli_val_style),
            ]
        )
    else:
        cli_rows.append(
            [
                Paragraph(doc_lbl, cli_label_style),
                Paragraph(doc_val, cli_val_style),
                '',
                '',
            ]
        )
        cli_spans.append(('SPAN', (1, 1), (3, 1)))

    # Sempre: inscrição estadual e e-mail (entre documento e endereço)
    row_ie_email = len(cli_rows)
    ie_txt = (getattr(cliente, 'inscricao_estadual', None) or '').strip()
    em_txt = (getattr(cliente, 'email', None) or '').strip()
    cli_rows.append(
        [
            Paragraph("Inscr. estadual", cli_label_style),
            Paragraph(escape(ie_txt) if ie_txt else '—', cli_val_style),
            Paragraph("E-mail", cli_label_style),
            Paragraph(escape(em_txt) if em_txt else '—', cli_val_style),
        ]
    )

    if cliente.endereco:
        row_endereco = len(cli_rows)
        ec = cliente.endereco
        if cliente.cep:
            ec += f" · CEP {cliente.cep}"
        if cliente.cidade and cliente.estado:
            ec += f" · {cliente.cidade}/{cliente.estado}"
        elif cliente.cidade:
            ec += f" · {cliente.cidade}"
        cli_rows.append(
            [
                Paragraph("Endereço", cli_label_style),
                Paragraph(escape(ec), cli_val_style),
                '',
                '',
            ]
        )
        cli_spans.append(('SPAN', (1, row_endereco), (3, row_endereco)))

    tbl_cliente = Table(cli_rows, colWidths=[w_c0, w_c1, w_c2, w_c3])
    borda_sutil = colors.HexColor('#d1d5db')
    st_cli = [
        ('BACKGROUND', (0, 0), (0, -1), fundo_lbl),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, borda_sutil),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, borda_sutil),
        ('LINEBEFORE', (0, 0), (0, -1), 0.5, borda_sutil),
        ('LINEAFTER', (-1, 0), (-1, -1), 0.5, borda_sutil),
    ]
    # Fundo cinza nas células de rótulo da 3ª coluna (Telefone / E-mail)
    if cliente.telefone:
        st_cli.append(('BACKGROUND', (2, 1), (2, 1), fundo_lbl))
        st_cli.append(('LINEBEFORE', (2, 1), (2, 1), 0.25, borda_sutil))
    st_cli.append(('BACKGROUND', (2, row_ie_email), (2, row_ie_email), fundo_lbl))
    st_cli.append(('LINEBEFORE', (2, row_ie_email), (2, row_ie_email), 0.25, borda_sutil))
    for r in range(len(cli_rows) - 1):
        st_cli.append(('LINEBELOW', (0, r), (-1, r), 0.35, borda_sutil))
    st_cli.extend(cli_spans)
    tbl_cliente.setStyle(TableStyle(st_cli))
    elements.append(tbl_cliente)
    elements.append(Spacer(1, SP + 0.1 * cm))
    
    if orcamento.descricao:
        elements.append(Paragraph("Descrição dos serviços", subtitulo_style))
        elements.append(Paragraph(orcamento.descricao, normal_style))
        elements.append(Spacer(1, SP))
    
    # Itens do Orçamento (Peças e Serviços)
    itens = orcamento.itens.all()
    if itens:
        elements.append(Paragraph("Itens do orçamento", secao_titulo_style))

        th_style = ParagraphStyle(
            'TabHead', parent=styles['Normal'],
            fontSize=7, fontName='Helvetica-Bold', textColor=colors.HexColor('#4b5563'),
            alignment=TA_CENTER, leading=9, **base_indent
        )
        th_left = ParagraphStyle(
            'TabHeadL', parent=styles['Normal'],
            fontSize=7, fontName='Helvetica-Bold', textColor=colors.HexColor('#4b5563'),
            alignment=TA_LEFT, leading=9, **base_indent
        )
        th_right = ParagraphStyle(
            'TabHeadR', parent=styles['Normal'],
            fontSize=7, fontName='Helvetica-Bold', textColor=colors.HexColor('#4b5563'),
            alignment=TA_RIGHT, leading=9, **base_indent
        )
        td_style = ParagraphStyle(
            'TabCell', parent=styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#111827'), leading=11, **base_indent
        )
        td_left = ParagraphStyle(
            'TabCellL', parent=td_style, alignment=TA_LEFT,
        )
        td_center = ParagraphStyle(
            'TabCellC', parent=td_style, alignment=TA_CENTER,
        )
        td_right = ParagraphStyle(
            'TabCellR', parent=td_style, alignment=TA_RIGHT,
        )

        dados_tabela = [
            [
                Paragraph('#', th_style),
                Paragraph('Tipo', th_left),
                Paragraph('Descrição', th_left),
                Paragraph('Qtd.', th_style),
                Paragraph('Valor unit.', th_right),
                Paragraph('Total', th_right),
            ],
        ]

        for idx, item in enumerate(itens, 1):
            dados_tabela.append(
                [
                    Paragraph(escape(str(idx)), td_center),
                    Paragraph(escape(item.get_tipo_display()), td_left),
                    Paragraph(escape(item.descricao or ''), td_left),
                    Paragraph(escape(str(item.quantidade)), td_center),
                    Paragraph(escape(f"R$ {_formatar_moeda(item.valor_unitario)}"), td_right),
                    Paragraph(escape(f"R$ {_formatar_moeda(item.valor_total)}"), td_right),
                ]
            )

        cw = [0.9 * cm, 2.1 * cm, 7.9 * cm, 1.8 * cm, 2.6 * cm, 2.7 * cm]
        tabela = Table(dados_tabela, colWidths=cw)

        fundo_cab = colors.HexColor('#e5e7eb')
        zebra_claro = colors.white
        zebra_cinza = colors.HexColor('#eef2f7')
        linha_grade = colors.HexColor('#94a3b8')
        linha_cab = colors.HexColor('#64748b')
        estilo_tabela = [
            ('BACKGROUND', (0, 0), (-1, 0), fundo_cab),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, 0), 1.25, linha_cab),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ]
        nrows = len(dados_tabela)
        # Zebrado contrastado + linhas horizontais visíveis (leitura à régua na impressão)
        for i in range(1, nrows):
            if i % 2 == 1:
                estilo_tabela.append(('BACKGROUND', (0, i), (-1, i), zebra_cinza))
            else:
                estilo_tabela.append(('BACKGROUND', (0, i), (-1, i), zebra_claro))
            estilo_tabela.append(('LINEBELOW', (0, i), (-1, i), 0.55, linha_grade))
        # Linhas verticais discretas em toda a tabela (alinhar colunas)
        for c in range(5):
            estilo_tabela.append(('LINEAFTER', (c, 0), (c, -1), 0.35, linha_grade))
        estilo_tabela.append(('LINEABOVE', (0, 0), (-1, 0), 0.35, linha_grade))
        tabela.setStyle(TableStyle(estilo_tabela))
        
        elements.append(tabela)
        elements.append(Spacer(1, SP))
        
        # Recalcular valor total (considera desconto/acréscimo)
        orcamento.calcular_valor_total()
        
        # Resumo de valores (subtotal, desconto, acréscimo, total)
        subtotal = orcamento.get_subtotal()
        valor_desconto = orcamento.get_valor_desconto_calculado()
        valor_acrescimo = orcamento.get_valor_acrescimo_calculado()
        
        valor_right_style = ParagraphStyle(
            'ValorRight', parent=styles['Normal'],
            fontSize=9, spaceAfter=2, alignment=TA_RIGHT, **base_indent
        )
        valor_total_style = ParagraphStyle(
            'ValorTotal', parent=styles['Normal'],
            fontSize=12, textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=4, alignment=TA_RIGHT, fontName='Helvetica-Bold', **base_indent
        )
        
        linhas_totais = [
            Paragraph(f"Subtotal: R$ {_formatar_moeda(subtotal)}", valor_right_style),
        ]
        if float(valor_desconto) > 0:
            desc_display = f"{orcamento.desconto}%" if orcamento.desconto_tipo == 'percentual' else ""
            linhas_totais.append(Paragraph(
                f"Desconto{' (' + desc_display + ')' if desc_display else ''}: - R$ {_formatar_moeda(valor_desconto)}",
                valor_right_style
            ))
        if float(valor_acrescimo) > 0:
            acresc_display = f"{orcamento.acrescimo}%" if orcamento.acrescimo_tipo == 'percentual' else ""
            linhas_totais.append(Paragraph(
                f"Acréscimo{' (' + acresc_display + ')' if acresc_display else ''}: + R$ {_formatar_moeda(valor_acrescimo)}",
                valor_right_style
            ))
        linhas_totais.append(Paragraph(f"<b>Valor total: R$ {_formatar_moeda(orcamento.valor_total)}</b>", valor_total_style))
        
        # Tabela de totais: uma coluna com largura total, parágrafos alinhados à direita
        tbl_totais = Table([[p] for p in linhas_totais], colWidths=[18*cm])
        tbl_totais.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(tbl_totais)
        elements.append(Spacer(1, SP))
    
    if orcamento.condicoes_pagamento:
        elements.append(Paragraph("Condições de pagamento", subtitulo_style))
        elements.append(Paragraph(orcamento.condicoes_pagamento, normal_style))
        elements.append(Spacer(1, SP))
    if orcamento.prazo_entrega:
        elements.append(Paragraph("Prazo de entrega / execução", subtitulo_style))
        elements.append(Paragraph(orcamento.prazo_entrega, normal_style))
        elements.append(Spacer(1, SP))
    if orcamento.observacoes:
        elements.append(Paragraph("Observações", subtitulo_style))
        elements.append(Paragraph(orcamento.observacoes, normal_style))
        elements.append(Spacer(1, SP))
    if empresa.observacoes_padrao:
        elements.append(Paragraph("Observações gerais", subtitulo_style))
        elements.append(Paragraph(empresa.observacoes_padrao, normal_style))
        elements.append(Spacer(1, SP))

    # Aceite: mesmo ritmo das demais seções (só o Spacer SP após o bloco anterior + spaceBefore do subtítulo)
    elements.append(Paragraph("Aceite do orçamento", subtitulo_style))
    assinatura_intro_style = ParagraphStyle(
        'AssinaturaIntro', parent=styles['Normal'],
        fontSize=9, spaceAfter=12, alignment=TA_LEFT, leading=13, **base_indent
    )
    elements.append(Paragraph(
        "Declaro estar de acordo com os valores, prazos e condições descritos neste orçamento, "
        "autorizando a execução dos serviços e/ou fornecimento conforme combinado.",
        assinatura_intro_style
    ))
    elements.append(Spacer(1, 0.45 * cm))
    assinatura_lbl_left = ParagraphStyle(
        'AssinaturaLblL', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=0, leading=9, **base_indent
    )
    assinatura_lbl_data = ParagraphStyle(
        'AssinaturaLblData', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=0, leading=9, **base_indent
    )
    cor_linha_ass = colors.HexColor('#374151')
    pad_lbl = 3
    st_inner = [
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]
    # Blocos separados: assinatura | vão | data (campo data só linha + rótulo, sem barras)
    w_ass_col = 9.3 * cm
    w_ass_gap = 1.6 * cm
    w_ass_data = LARGURA_UTIL - w_ass_col - w_ass_gap
    h_faixa_linha = 0.72 * cm  # mesma altura nos dois blocos = traços alinhados
    tbl_assinatura_esq = Table(
        [
            [''],
            [Paragraph('Assinatura do cliente', assinatura_lbl_left)],
        ],
        colWidths=[w_ass_col],
        rowHeights=[h_faixa_linha, None],
    )
    tbl_assinatura_esq.setStyle(TableStyle([
        *st_inner,
        ('VALIGN', (0, 0), (0, 0), 'BOTTOM'),
        ('VALIGN', (0, 1), (0, 1), 'TOP'),
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('LINEBELOW', (0, 0), (0, 0), 0.7, cor_linha_ass),
        ('TOPPADDING', (0, 1), (0, 1), pad_lbl),
    ]))
    tbl_assinatura_dir = Table(
        [
            [''],
            [Paragraph('Data', assinatura_lbl_data)],
        ],
        colWidths=[w_ass_data],
        rowHeights=[h_faixa_linha, None],
    )
    tbl_assinatura_dir.setStyle(TableStyle([
        *st_inner,
        ('VALIGN', (0, 0), (0, 0), 'BOTTOM'),
        ('VALIGN', (0, 1), (0, 1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('LINEBELOW', (0, 0), (0, 0), 0.7, cor_linha_ass),
        ('TOPPADDING', (0, 1), (0, 1), pad_lbl),
    ]))
    tbl_assinatura = Table(
        [[tbl_assinatura_esq, '', tbl_assinatura_dir]],
        colWidths=[w_ass_col, w_ass_gap, w_ass_data],
    )
    tbl_assinatura.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, 0), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(tbl_assinatura)

    rodape_canvas_style = ParagraphStyle(
        'RodapeOrcamentoCanvas',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        leading=10,
        spaceBefore=0,
        spaceAfter=0,
        **base_indent,
    )

    def _rodape_todas_paginas(canvas, doc_tpl):
        """Desenha texto_rodape no rodapé físico de cada página (abaixo do fluxo)."""
        if not texto_rodape_pdf:
            return
        canvas.saveState()
        try:
            p = Paragraph(escape(texto_rodape_pdf), rodape_canvas_style)
            altura_max = max(doc_tpl.bottomMargin - 0.25 * cm, 0.35 * cm)
            _sw, sh = p.wrap(doc_tpl.width, altura_max)
            y = doc_tpl.bottomMargin - sh - 0.12 * cm
            if y < 0.2 * cm:
                y = 0.2 * cm
            p.drawOn(canvas, doc_tpl.leftMargin, y)
        finally:
            canvas.restoreState()

    # Construir PDF (rodapé em onFirstPage + onLaterPages)
    doc.build(elements, onFirstPage=_rodape_todas_paginas, onLaterPages=_rodape_todas_paginas)
    
    # Obter o valor do buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Criar resposta HTTP - nome: ORC-005 - GOOGLE BRASIL INTERNET LTDA.pdf
    razao_social = (orcamento.cliente.razao_social or '').replace('/', '-').replace('\\', '-').replace(':', '-')
    razao_social = ''.join(c for c in razao_social if c not in '*?"<>|')
    nome_arquivo = f"{orcamento.numero} - {razao_social.strip() or 'Orcamento'}.pdf"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    # Evita PDF antigo em cache após deploy / alteração do layout
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response.write(pdf)
    
    return response
