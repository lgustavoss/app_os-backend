"""Normalização e validação de documentos (CNPJ/CPF) para evitar duplicatas com máscaras diferentes."""


def only_digits(value):
    if value is None:
        return ''
    return ''.join(c for c in str(value) if c.isdigit())


def empresa_cnpj_duplicado(cnpj_value, exclude_pk=None):
    """Retorna True se já existir empresa com o mesmo CNPJ (apenas dígitos)."""
    from configuracoes.models import ConfiguracaoEmpresa

    digits = only_digits(cnpj_value)
    if len(digits) != 14:
        return False
    qs = ConfiguracaoEmpresa.objects.all()
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    for obj in qs.iterator():
        if only_digits(obj.cnpj) == digits:
            return True
    return False


def cliente_documento_duplicado(cnpj_cpf_value, exclude_pk=None):
    """Retorna True se já existir cliente com o mesmo CNPJ/CPF (apenas dígitos)."""
    from clientes.models import Cliente

    digits = only_digits(cnpj_cpf_value)
    if not digits:
        return False
    qs = Cliente.objects.all()
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    for obj in qs.iterator():
        if only_digits(obj.cnpj_cpf) == digits:
            return True
    return False
